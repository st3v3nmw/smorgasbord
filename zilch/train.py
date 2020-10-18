from random import randint, random
import matplotlib.pyplot as plt

class Agent:
    def __init__(self, fitness: int, sh: int, lo: int):
        self.short = sh
        self.long = lo
        self.fitness = fitness
        self.units = 0

        if self.short > self.long:
            self.short, self.long = self.long, self.short
        
    def __repr__(self):
        return f"({round(self.fitness, 2)}, {self.short}, {self.long})"

class Population:
    def __init__(self, n: int, fitness: int, r: float, data: list):
        self.n = n
        self.d_len = int(0.25 * len(data))
        self.agents = [Agent(fitness, randint(1, self.d_len), randint(1, self.d_len)) for _ in range(n)]
        self.data = data
        self.r = r
        self.fitness = fitness
    
    def __repr__(self):
        return f"{self.agents}"

    def new_agent(self, parent):
        sh, lo = parent.short, parent.long
        # mutation
        if random() < self.r:
            sh = randint(1, self.d_len)
        if random() < self.r:
            lo = randint(1, self.d_len)
        agent = Agent(self.fitness, sh, lo)
        agent.short = agent.short if agent.short > 0 else 1
        agent.long = agent.long if agent.long > 0 else 1
        if agent.short > agent.long:
            agent.short, agent.long = agent.long, agent.short
        return agent

    def simulate_best(self):
        buys, sells = [[], []], [[], []]
        agent = self.agents[0]
        sh = sum(self.data[agent.long-agent.short:agent.long])
        lo = sum(self.data[:agent.long])
        for i in range(agent.long, len(self.data)):
            sh += self.data[i] - self.data[i - agent.short]
            lo += self.data[i] - self.data[i - agent.long]
            if sh / agent.short > lo / agent.long and agent.units == 0:
                agent.units = agent.fitness / self.data[i]
                agent.fitness = 0
                buys[0].append(i)
                buys[1].append(self.data[i])
            elif sh / agent.short < lo / agent.long and agent.units > 0:
                agent.fitness = agent.units * self.data[i]
                agent.units = 0
                sells[0].append(i)
                sells[1].append(self.data[i])
        return buys, sells
    
    def steps(self, n: int):
        for j in range(n):
            for agent in self.agents:
                sh = sum(self.data[agent.long-agent.short:agent.long])
                lo = sum(self.data[:agent.long])
                for i in range(agent.long, len(self.data)):
                    sh += self.data[i] - self.data[i - agent.short]
                    lo += self.data[i] - self.data[i - agent.long]

                    if sh / agent.short > lo / agent.long and agent.units == 0:
                        agent.units = (0.995 * agent.fitness) / self.data[i]
                        agent.fitness = 0
                    elif sh / agent.short < lo / agent.long and agent.units > 0:
                        agent.fitness = 0.995 * agent.units * self.data[i]
                        agent.units = 0
                agent.fitness = agent.units * self.data[len(self.data) - 1]
                agent.units = 0
            
            self.agents.sort(key=lambda x: x.fitness, reverse=True)
            print(self.agents[0])
            if j < n - 1:
                # selection
                parents = self.agents[:int(self.n / 2)]
                self.agents = []
                for parent in parents:
                    self.agents.append(self.new_agent(parent))
                    self.agents.append(self.new_agent(parent))

        return self.simulate_best()


data = list(map(float, open("in.txt", "r").readlines()))

pp = Population(64, 1000, 0.16, data)
buys, sells = pp.steps(32)
# print(buys, sells)

plt.plot(data)
plt.scatter(buys[0], buys[1], c = 'green', s = 16)
plt.scatter(sells[0], sells[1], c = 'red', s = 16)
plt.show()