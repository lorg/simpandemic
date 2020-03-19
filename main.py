import time
import math
import random
import dataclasses
import collections
from typing import Dict, Tuple, List

import pygame

MAX_X = 100
MAX_Y = 100


def constrain(v, max_v):
    if v < 0:
        v = 0
    if v > max_v:
        v = max_v
    return v


def get_neighbours(cell):
    cell_x, cell_y = cell
    yield cell_x, cell_y + 1
    yield cell_x + 1, cell_y + 1
    yield cell_x + 1, cell_y
    if cell_y > 0:
        yield cell_x + 1, cell_y - 1
        yield cell_x, cell_y
    if cell_x > 0:
        yield cell_x - 1, cell_y
        yield cell_x - 1, cell_y + 1
    if cell_x > 0 and cell_y > 0:
        yield cell_x - 1, cell_y - 1


@dataclasses.dataclass
class Disease:
    max_transmission_distance: float
    transmission_rate: float
    fatality_rate: float
    duration: int
    reinfection_ratio: float


class Human:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.is_infected = False
        self.infected_on = None
        self.is_alive = True

    def move(self, max_x, max_y):
        self.x += random.randint(-3, 3)
        self.x = constrain(self.x, max_x)
        self.y += random.randint(-3, 3)
        self.y = constrain(self.y, max_y)

    def distance(self, other: "Human"):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5


@dataclasses.dataclass
class Stats:
    sick: int = 0
    healthy: int = 0
    recovered: int = 0
    dead: int = 0
    alive: int = 0


class Simulator:
    def __init__(self, num_humans, disease):
        self.step_num = 0
        self.disease = disease
        self.humans = []
        for i in range(num_humans):
            self.humans.append(Human(
                random.randint(0, MAX_X),
                random.randint(0, MAX_Y)
            ))

    def seed_infection(self, num_infected):
        to_infect = random.choices(self.humans, k=num_infected)
        for human in to_infect:
            human.is_infected = True
            human.infected_on = self.step_num

    def stats(self):
        result = Stats()
        for human in self.humans:
            if human.is_alive:
                result.alive += 1
            else:
                result.dead += 1
                continue
            if human.is_infected:
                result.sick += 1
            elif human.infected_on is None:
                result.healthy += 1
            else:
                result.recovered += 1
        return result

    def step(self):
        self.step_num += 1
        for human in self.humans:
            if not human.is_alive:
                continue
            if human.is_infected and self.step_num - human.infected_on >= self.disease.duration:
                if random.random() < self.disease.fatality_rate:
                    human.is_alive = False
                else:
                    human.is_infected = False

            if human.is_alive:
                human.move(MAX_X, MAX_Y)

        cells: Dict[Tuple[int, int], Tuple[List[Human], List[Human]]] = collections.defaultdict(lambda: ([], []))
        for human in self.humans:
            if not human.is_alive:
                continue
            cell_x = int(math.ceil(human.x / self.disease.max_transmission_distance))
            cell_y = int(math.ceil(human.y / self.disease.max_transmission_distance))
            if human.is_infected:
                cells[(cell_x, cell_y)][0].append(human)
            else:
                cells[(cell_x, cell_y)][1].append(human)

        for cell, (infected, healthy) in list(cells.items()):
            neighbours = list(get_neighbours(cell))
            total_infected = infected + sum((cells[neighbour][0] for neighbour in neighbours), [])
            num_infected = len(total_infected)
            for healthy_human in healthy:
                ratio = self.disease.transmission_rate \
                    if healthy_human.infected_on is None else self.disease.reinfection_ratio
                for sick_human in total_infected:
                    if healthy_human.distance(sick_human) > self.disease.max_transmission_distance:
                        continue
                    # chance_of_infection = 1 - ((1 - ratio) ** num_infected)
                    # healthy_human.is_infected = random.random() < chance_of_infection
                    healthy_human.is_infected = random.random() < ratio
                    if healthy_human.is_infected:
                        healthy_human.infected_on = self.step_num
                        break


HEALTHY_COLOR = (0, 0, 0)
INFECTED_COLOR = (255, 0, 0)
HEALED_COLOR = (0, 255, 0)
DEAD_COLOR = (200, 200, 200)
BG_COLOR = (255, 255, 255)
FPS = 30

SCREEN_X = 500
SCREEN_Y = 500


def main():
    ccc = Disease(
        max_transmission_distance=15,
        transmission_rate=0.1,
        fatality_rate=0.1,
        duration=15,
        reinfection_ratio=0.01
    )
    simulator = Simulator(100, ccc)
    simulator.seed_infection(1)
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_X, SCREEN_Y))
    clock = pygame.time.Clock()
    try:
        while True:
            # clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            simulator.step()
            screen.fill(BG_COLOR)
            stats = simulator.stats()
            print(f"SIMULATOR STEP {simulator.step_num}\n\t{stats}")
            if stats.sick == 0 or stats.alive == 0:
                break
            for human in simulator.humans:
                if not human.is_alive:
                    color = DEAD_COLOR
                elif human.is_infected:
                    color = INFECTED_COLOR
                elif human.infected_on is None:
                    color = HEALTHY_COLOR
                else:
                    color = HEALED_COLOR
                pos_x = int(float(human.x / MAX_X) * SCREEN_X)
                pos_y = int(float(human.y / MAX_Y) * SCREEN_Y)
                pygame.draw.circle(screen, color, (pos_x, pos_y), 5)
            pygame.display.flip()

    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
