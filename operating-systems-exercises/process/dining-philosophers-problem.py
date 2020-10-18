""" Philosopher 4 always dies :( """
""" Problem to fix: This works in a round robin manner, while in real life the philosophers would make their decisions concurrently """

class Mutex:
    def __init__(self):
        self.value = False

    def acquire(self):
        if self.value:
            return False
        else:
            self.value = True
            return True

    def release(self):
        if self.value:
            self.value = False

    def __repr__(self):
        return f"{self.value}"

class Philosopher:
    THINKING, EATING, HUNGRY, DEAD = 0, 1, 2, 3
    def __init__(self, position):
        self.position = position
        # if energy < 25, eat until energy = 100; if energy == 0, starve to death :(
        self.energy = 32
        self.state = self.THINKING

    def acquire_chopsticks(self):
        chopstick1 = chopsticks[self.position].acquire()
        chopstick2 = chopsticks[(self.position + 1) % 5].acquire()
        if chopstick1:
            if chopstick2:
                return True

        # if s/he didn't get both chopsticks, release any that s/he is holding
        if chopstick1:
            chopsticks[self.position].release()
        if chopstick2:
            chopsticks[(self.position + 1) % 5].release()
        return False

    def loop(self):
        if self.state == self.DEAD:
            return
        
        if self.energy < 25: # philosopher's hungry
            if self.state != self.EATING: # check previous state
                if self.acquire_chopsticks(): # we acquired both chopsticks
                    self.state = self.EATING
                else:
                    self.state = self.HUNGRY

        if self.state == self.THINKING:
            self.energy -= 1
        elif self.state == self.HUNGRY:
            self.energy -= 0.5
        else:
            if self.energy >= 100:
                chopsticks[self.position].release()
                chopsticks[(self.position + 1) % 5].release()
                self.state = self.THINKING
            else:
                self.energy += 2

        if self.energy == 0:
            self.state = self.DEAD

    def state_text(self):
        states = ["THINKING", "EATING", "HUNGRY", "DEAD"]
        return states[self.state]
    def __repr__(self):
        return f"Philosopher {self.position}, {self.energy}, {self.state_text()}"


chopsticks = [Mutex(), Mutex(), Mutex(), Mutex(), Mutex()]
philosophers = [Philosopher(0), Philosopher(1), Philosopher(2), Philosopher(3), Philosopher(4)]

for i in range(100):
    print(f"\nIteration {i}")
    for philosopher in philosophers:
        philosopher.loop()
        print(philosopher)
    for chopstick in chopsticks:
        print(chopstick, end=" ")
    print("\n")