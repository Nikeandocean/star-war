"""GPU-accelerated renderer using OpenGL shaders.

Provides:
- Procedural nebula background (fragment shader)
- Post-processing: vignette, flash overlay, screen shake
- Pygame surface → GL texture compositing
"""

import ctypes
import numpy as np

try:
    from OpenGL.GL import *
    from OpenGL.GL import shaders
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False

import pygame

# ─── Shader sources ────────────────────────────────────────────────

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aUV;
out vec2 vUV;
void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

# Procedural nebula background — flowing clouds + star field
BACKGROUND_SHADER = """
#version 330 core
in vec2 vUV;
out vec4 FragColor;

uniform float uTime;
uniform vec2 uResolution;

// Simplex-style noise (fast 2D)
vec2 hash(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(dot(hash(i + vec2(0,0)), f - vec2(0,0)),
                   dot(hash(i + vec2(1,0)), f - vec2(1,0)), u.x),
               mix(dot(hash(i + vec2(0,1)), f - vec2(0,1)),
                   dot(hash(i + vec2(1,1)), f - vec2(1,1)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p = rot * p * 2.0;
        a *= 0.5;
    }
    return v;
}

// Star field layer
float stars(vec2 uv, float scale, float density, float brightness) {
    vec2 id = floor(uv * scale);
    vec2 gv = fract(uv * scale) - 0.5;
    float h = fract(sin(dot(id, vec2(12.9898, 78.233))) * 43758.5453);
    if (h > density) return 0.0;
    float d = length(gv - (hash(id) * 0.3));
    float star = smoothstep(0.08, 0.0, d);
    // Twinkle
    float twinkle = 0.5 + 0.5 * sin(uTime * (1.0 + h * 3.0) + h * 6.28);
    return star * brightness * twinkle;
}

void main() {
    vec2 uv = vUV;
    vec2 aspect = vec2(uResolution.x / uResolution.y, 1.0);
    vec2 p = uv * aspect;

    float t = uTime * 0.02;

    // ── Nebula layers ──
    // Deep base — dark purple/blue
    float n1 = fbm(p * 1.5 + vec2(t * 0.3, t * 0.1));
    vec3 col1 = mix(vec3(0.02, 0.01, 0.06), vec3(0.04, 0.02, 0.12), n1);

    // Mid layer — blue/teal clouds
    float n2 = fbm(p * 2.0 + vec2(-t * 0.2, t * 0.15) + 5.0);
    vec3 col2 = mix(vec3(0.0, 0.04, 0.1), vec3(0.0, 0.08, 0.15), n2);
    col1 += col2 * 0.6;

    // Bright layer — purple/magenta wisps
    float n3 = fbm(p * 3.0 + vec2(t * 0.1, -t * 0.2) + 10.0);
    float wisps = smoothstep(0.3, 0.7, n3);
    col1 += wisps * vec3(0.12, 0.02, 0.08) * 0.5;

    // Warm accent — orange/amber
    float n4 = fbm(p * 2.5 + vec2(t * 0.15, t * 0.05) + 15.0);
    float warm = smoothstep(0.5, 0.8, n4);
    col1 += warm * vec3(0.08, 0.04, 0.01) * 0.4;

    // Teal highlights
    float n5 = fbm(p * 4.0 + vec2(-t * 0.1, t * 0.25) + 20.0);
    float teal = smoothstep(0.45, 0.75, n5);
    col1 += teal * vec3(0.0, 0.06, 0.08) * 0.3;

    // ── Stars ──
    float s1 = stars(uv, 80.0, 0.7, 0.8);   // far layer — many small
    float s2 = stars(uv, 40.0, 0.6, 1.0);   // mid layer
    float s3 = stars(uv, 20.0, 0.5, 1.2);   // near layer — fewer, brighter
    float all_stars = s1 + s2 + s3;
    // Subtle color tint on stars
    vec3 star_col = vec3(0.9, 0.92, 1.0) * all_stars;
    col1 += star_col;

    // ── Occasional bright star ──
    float bright_h = fract(sin(dot(floor(uv * 10.0), vec2(12.9898, 78.233))) * 43758.5453);
    if (bright_h > 0.995) {
        float bright_star = stars(uv, 10.0, 1.0, 2.0);
        col1 += bright_star * vec3(1.0, 0.95, 0.8);
    }

    FragColor = vec4(col1, 1.0);
}
"""

# Post-processing: chroma-key composite + vignette + flash + screen shake
POST_SHADER = """
#version 330 core
in vec2 vUV;
out vec4 FragColor;

uniform sampler2D uGameTex;
uniform sampler2D uBgTex;
uniform float uVignetteAlpha;
uniform float uFlashAlpha;
uniform vec2 uShakeOffset;

void main() {
    vec2 uv = vUV + uShakeOffset;
    uv = clamp(uv, 0.0, 1.0);

    vec4 game = texture(uGameTex, uv);
    vec3 bg = texture(uBgTex, vUV).rgb;

    // Chroma key: replace near-black game pixels with background
    float brightness = dot(game.rgb, vec3(0.299, 0.587, 0.114));
    float mask = smoothstep(0.0, 0.02, brightness);
    vec3 color = mix(bg, game.rgb, mask);

    // Vignette — darken edges
    vec2 vigUV = vUV * 2.0 - 1.0;
    float vig = 1.0 - dot(vigUV * 0.5, vigUV * 0.5);
    vig = clamp(vig, 0.0, 1.0);
    color *= mix(1.0, vig, uVignetteAlpha);

    // Red vignette tint when taking damage
    if (uVignetteAlpha > 0.0) {
        float edge = 1.0 - vig;
        color += vec3(0.3, 0.0, 0.0) * edge * uVignetteAlpha;
    }

    // Flash overlay (additive white)
    color += vec3(uFlashAlpha);

    FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""

# Simple passthrough for blitting textures
BLIT_SHADER = """
#version 330 core
in vec2 vUV;
out vec4 FragColor;
uniform sampler2D uTex;
void main() {
    FragColor = texture(uTex, vUV);
}
"""


# ─── Renderer ──────────────────────────────────────────────────────

class GLRenderer:
    """OpenGL rendering backend for background and post-processing."""

    def __init__(self, width, height):
        if not HAS_OPENGL:
            raise RuntimeError("PyOpenGL not installed. Run: pip install PyOpenGL")

        self.width = width
        self.height = height

        # Compile shaders
        self.bg_program = self._compile_shader(VERTEX_SHADER, BACKGROUND_SHADER)
        self.post_program = self._compile_shader(VERTEX_SHADER, POST_SHADER)

        # Fullscreen quad geometry
        self.vao, self.vbo = self._create_quad()

        # Game surface texture (uploaded each frame)
        self.game_tex = self._create_texture()
        # Background render texture
        self.bg_tex = self._create_texture()
        # Framebuffer for rendering background to texture
        self.fbo = glGenFramebuffers(1)

        # Uniform locations — background
        self.u_bg_time = glGetUniformLocation(self.bg_program, "uTime")
        self.u_bg_resolution = glGetUniformLocation(self.bg_program, "uResolution")

        # Uniform locations — post-processing
        self.u_post_game_tex = glGetUniformLocation(self.post_program, "uGameTex")
        self.u_post_bg_tex = glGetUniformLocation(self.post_program, "uBgTex")
        self.u_post_vignette = glGetUniformLocation(self.post_program, "uVignetteAlpha")
        self.u_post_flash = glGetUniformLocation(self.post_program, "uFlashAlpha")
        self.u_post_shake = glGetUniformLocation(self.post_program, "uShakeOffset")

        # GL state
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)

    def _create_texture(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex

    def _compile_shader(self, vert_src, frag_src):
        vert = shaders.compileShader(vert_src, GL_VERTEX_SHADER)
        frag = shaders.compileShader(frag_src, GL_FRAGMENT_SHADER)
        program = shaders.compileProgram(vert, frag)
        return program

    def _create_quad(self):
        # Position (x,y) + UV (u,v) — fullscreen quad
        vertices = np.array([
            -1, -1,  0, 0,
             1, -1,  1, 0,
             1,  1,  1, 1,
            -1, -1,  0, 0,
             1,  1,  1, 1,
            -1,  1,  0, 1,
        ], dtype=np.float32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Position attribute
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # UV attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)
        return vao, vbo

    def draw_background(self, time):
        """Render procedural nebula background to texture via FBO."""
        # Bind FBO and render background shader to bg_tex
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                               GL_TEXTURE_2D, self.bg_tex, 0)

        glUseProgram(self.bg_program)
        glUniform1f(self.u_bg_time, time)
        glUniform2f(self.u_bg_resolution, self.width, self.height)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        # Unbind FBO (back to default framebuffer)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def upload_game_surface(self, surface):
        """Upload a pygame surface to the GL game texture."""
        data = pygame.image.tostring(surface, "RGBA", True)  # flipped
        glBindTexture(GL_TEXTURE_2D, self.game_tex)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                        GL_RGBA, GL_UNSIGNED_BYTE, data)
        glBindTexture(GL_TEXTURE_2D, 0)

    def composite_and_postprocess(self, vignette_alpha=0.0, flash_alpha=0.0,
                                   shake_x=0.0, shake_y=0.0):
        """Composite game over background via chroma key, apply post-processing."""
        glUseProgram(self.post_program)

        # Bind game texture to unit 0
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.game_tex)
        glUniform1i(self.u_post_game_tex, 0)

        # Bind background texture to unit 1
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.bg_tex)
        glUniform1i(self.u_post_bg_tex, 1)

        glUniform1f(self.u_post_vignette, vignette_alpha)
        glUniform1f(self.u_post_flash, flash_alpha)
        glUniform2f(self.u_post_shake, shake_x, shake_y)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)

    def cleanup(self):
        """Release GL resources."""
        glDeleteTextures([self.game_tex, self.bg_tex])
        glDeleteFramebuffers(1, [self.fbo])
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteProgram(self.bg_program)
        glDeleteProgram(self.post_program)


def is_available():
    """Check if OpenGL rendering is available."""
    return HAS_OPENGL
