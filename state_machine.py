"""State machine framework for game state management."""


class State:
    """Base class for game states."""

    def __init__(self, machine):
        self.machine = machine

    def enter(self):
        """Called when this state becomes active."""

    def exit(self):
        """Called when this state is being deactivated."""

    def handle_events(self, events):
        """Process a list of pygame events."""

    def update(self):
        """Update game logic."""

    def draw(self, screen):
        """Render to screen."""


class StateMachine:
    """Manages a stack of states. Push/pop supports pause-style overlays."""

    def __init__(self):
        self.stack = []
        self.pending_transitions = []

    @property
    def current(self):
        return self.stack[-1] if self.stack else None

    def push(self, state):
        """Push a new state on top (e.g. pause over gameplay)."""
        self.pending_transitions.append(('push', state))

    def pop(self):
        """Remove the top state and resume the one below."""
        self.pending_transitions.append(('pop', None))

    def switch(self, state):
        """Replace the current state entirely."""
        self.pending_transitions.append(('switch', state))

    def _apply_transitions(self):
        for action, state in self.pending_transitions:
            if action == 'push':
                if self.stack:
                    self.current.exit()
                self.stack.append(state)
                state.enter()
            elif action == 'pop':
                if self.stack:
                    self.current.exit()
                    self.stack.pop()
                if self.stack:
                    self.current.enter()
            elif action == 'switch':
                if self.stack:
                    self.current.exit()
                    self.stack.pop()
                self.stack.append(state)
                state.enter()
        self.pending_transitions.clear()

    def handle_events(self, events):
        self._apply_transitions()
        if self.current:
            self.current.handle_events(events)

    def update(self):
        self._apply_transitions()
        if self.current:
            self.current.update()

    def draw(self, screen):
        # Draw all states in stack order (bottom to top) for overlay effects
        for state in self.stack:
            state.draw(screen)
