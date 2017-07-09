import numpy as np
import collections

from deap import creator, base, benchmarks

constrain = collections.namedtuple('constrain', 'min max step')
solution = collections.namedtuple('solution', 'position error')

creator.create("Particle", object, parent=None, history_length=None, position=None, solution_history=None,
               best_solution=None, current_error=None)
creator.create("Tribe", object, shaman=None, is_good=False, members=None, informers=list,
               historical_best_error=None)


def plane(data):
    return data[0]


def generate_new_position(constraints):
    position = []
    for _ in constraints:
        position.append(125)
    return np.array(position)


def generate_new_particle(factory, history_length):
    particle = factory()
    position = toolbox.position()
    error = toolbox.evaluate(position)

    particle.position = position
    particle.current_error = error
    particle.history_length = history_length
    particle.best_solution = solution(position, error)
    particle.solution_history = [False for _ in range(history_length)]

    return particle


def generate_new_tribe(factory, members):
    tribe = factory()
    tribe.members = members

    for p in tribe.members:
        if p is None:
            raise TypeError("members cannot contain any null items")
        p.parent = tribe

    update_shaman(tribe)
    tribe.historical_best_error = tribe.shaman.best_solution.error
    update_is_good(tribe)

    return tribe


toolbox = base.Toolbox()
toolbox.register("position", generate_new_position, constraints=[constrain(1, 5, 1), constrain(10, 25, 5)])
toolbox.register("particle", generate_new_particle, creator.Particle, history_length=2)
toolbox.register("tribe", generate_new_tribe, creator.Tribe)
toolbox.register("evaluate", plane)


def calculate_center_of_gravity(point1, point2, point1_mass=1, point2_mass=1):
    new_points = list(map(lambda p1, p2: (p1 * point1_mass + p2 * point2_mass) /
                                         (point1_mass + point2_mass), point1, point2))
    return np.array(new_points)


def is_particle_excellent(particle):
    if len(particle.solution_history) < 2:
        return False
    else:
        return particle.solution_history[0] and particle.solution_history[1]


def calculate_new_position(particle, best_informer_solution):
    #How to  generates integer values in a given range.


def get_external_informers(particle):
    if particle.parent is None or particle.parent.shaman != particle:
        return []
    else:
        return [informer.shaman for informer in particle.parent.informers]


def get_internal_informers(particle):
    if particle.parent is None:
        return [particle]
    else:
        return particle.parent.members


def get_swarm_size(tribes):
    return sum(len(tribe.members) for tribe in tribes)


def get_tribes_in_random_order(tribes, rng):
    random_order = {rng.random(): tribe for tribe in tribes}
    return [v for k, v in sorted(random_order.items())]


def update_shaman(tribe):
    data = sorted(tribe.members, key=lambda x: x.best_solution.error)
    tribe.shaman = next(iter(data))


def update_is_good(tribe):
    if tribe.shaman.best_solution.error < tribe.historical_best_error:
        tribe.is_good = True
        tribe.historical_best_error = tribe.shaman.best_solution.error
    else:
        tribe.is_good = False


def move_particle(particle):
    informers = get_internal_informers(particle) + get_external_informers(particle)
    sorted_informers = sorted(informers, key=lambda x: x.best_solution.error)
    best_informer = next(iter(sorted_informers))

    if best_informer != particle:
        best_informer_solution = best_informer.best_solution
        new_position = calculate_new_position(particle, best_informer_solution)
        new_error = toolbox.evaluate(new_position)

        improved_best_solution = new_error < particle.best_solution.error

        if improved_best_solution:
            particle.best_solution = solution(new_position, new_error)

        particle.solution_history.insert(0, improved_best_solution)
        del particle.solution_history[particle.history_length:len(particle.solution_history)]

        particle.position = new_position
        particle.current_error = new_error


def move_swarm(tribes, rng):
    for tribe in get_tribes_in_random_order(tribes, rng):
        for particle in tribe.members:
            move_particle(particle)


def is_swarm_require_adaptation(tribes, moves_since_adaptation):
    number_of_links = 0
    for tribe in tribes:
        internal_link_count = len(tribe.members) * len(tribe.members)
        external_link_count = len(tribe.informers)
        number_of_links += internal_link_count + external_link_count

    adaptation_interval = number_of_links / 4
    return moves_since_adaptation >= adaptation_interval


def add_informer_to_tribe(tribe, informer):
    if informer is None:
        raise TypeError("informer")
    if informer in tribe.informers or informer == tribe:
        return
    else:
        tribe.informers.append(informer)
        add_informer_to_tribe(informer, tribe)


def redistribute_links(source, destination):
    for informer_tribe in source.informers:
        informer_tribe.informers.remove(source)
        add_informer_to_tribe(informer_tribe, destination)
        add_informer_to_tribe(destination, informer_tribe)
    del source.informers[:]


def try_remove_worst_particle(tribe):
    if len(tribe.members) > 1:
        sorted_members = sorted(tribe.members, reverse=True, key=lambda x: x.best_solution.error)
        worst_tribe_member = next(iter(sorted_members))
        tribe.members.remove(worst_tribe_member)
        removed_particle = True
    elif len(tribe.members) == 1:
        if any(o.best_solution.error < tribe.best_solution.error for o in tribe.informers):
            sorted_tribes = sorted(tribe.informers, key=lambda x: x.best_solution.error)
            best_informer_tribe = next(iter(sorted_tribes))
            redistribute_links(tribe, best_informer_tribe)
            del tribe.members[:]
            removed_particle = True
        else:
            removed_particle = False
    else:
        removed_particle = False
    return removed_particle


def adapt_swarm(tribes):
    good_tribes = filter(lambda x: x.is_good, tribes)
    for tribe in good_tribes:
        try_remove_worst_particle(tribe)
    empty_tribes = list(filter(lambda x: len(x.members) == 0, tribes))
    for tribe in empty_tribes:
        tribes.remove(tribe)
    bad_tribes = list(filter(lambda x: not x.is_good, tribes))
    if len(bad_tribes) > 0:
        tribe_members = [toolbox.particle() for _ in bad_tribes]
        new_tribe = toolbox.tribe(tribe_members)
        for bad_tribe in bad_tribes:
            add_informer_to_tribe(bad_tribe, new_tribe)
        tribes.append(new_tribe)


def main():
    rng = None
    tribes = []
    generations = 2500
    moves_since_adaptation = 0

    for generation in range(generations):
        if get_swarm_size(tribes) == 0:
            particle = toolbox.particle()
            tribe = toolbox.tribe([particle])
            tribes.append(tribe)
        else:
            move_swarm(tribes, rng)
            moves_since_adaptation += 1
            for tribe in tribes:
                update_shaman(tribe)
        if is_swarm_require_adaptation(tribes, moves_since_adaptation):
            adapt_swarm(tribes)


if __name__ == "__main__":
    main()
