from random import Random
from _pytest.monkeypatch import MonkeyPatch

from tribes import *

from mock import Mock


def test_get_swarm_size():
    tribes = []
    for _ in range(4):
        tribe = Mock()
        tribe.members = [None, None]
        tribes.append(tribe)

    assert get_swarm_size(tribes) == 8


def test_init_particle():
    error = 125
    history_length = 2
    position = np.array([125, 125])
    solution_history = [False, False]
    particle = toolbox.particle()

    assert np.all(particle.position == position)
    assert particle.current_error == error
    assert particle.history_length == history_length
    assert np.all(particle.best_solution.position == position)
    assert particle.best_solution.error == error
    assert particle.solution_history == solution_history


def test_init_tribe():
    particle_1 = Mock()
    particle_2 = Mock()
    particle_1.best_solution.error = 1
    particle_2.best_solution.error = 2
    members = [particle_1, particle_2]

    tribe = toolbox.tribe(members=members)

    assert tribe.is_good == False
    assert tribe.shaman == particle_1


def test_update_shaman():
    tribe = Mock()
    particle_1 = Mock()
    particle_2 = Mock()

    tribe.shaman = None
    particle_1.best_solution.error = 1
    particle_2.best_solution.error = 2

    tribe.members = [particle_1, particle_2]
    update_shaman(tribe)
    assert tribe.shaman == particle_1


def test_update_is_good_change_status_to_true():
    tribe = Mock()
    tribe.is_good = False
    tribe.historical_best_error = 15
    tribe.shaman.best_solution.error = 10

    update_is_good(tribe)
    assert tribe.is_good == True


def test_update_is_good_change_status_to_false():
    tribe = Mock()
    tribe.is_good = True
    tribe.historical_best_error = 10
    tribe.shaman.best_solution.error = 15

    update_is_good(tribe)
    assert tribe.is_good == False


def test_move_particle():
    tribe = Mock()
    particle_1 = Mock()
    particle_2 = Mock()
    tribe.shaman = Mock()

    particle_1.best_solution = solution([1, 2], 2)
    particle_2.best_solution = solution([3, 4], 1)
    particle_1.history_length = 2
    particle_2.history_length = 2
    particle_1.solution_history = [False, False]
    particle_2.solution_history = [False, False]

    tribe.members = [particle_1, particle_2]

    particle_1.parent = tribe
    move_particle(particle_1)

    assert particle_1.position == [3, 4]
    assert particle_1.current_error == 3


def test_get_tribes_in_random_order():
    tribe_1 = Mock()
    tribe_2 = Mock()
    tribe_3 = Mock()

    random = Random(777)
    tribes = [tribe_1, tribe_2, tribe_3]
    tribes_in_random_order = get_tribes_in_random_order(tribes, random)

    assert tribes_in_random_order == [tribe_1, tribe_3, tribe_2]


def test_get_external_informers_return_filled_list():
    tribe = Mock()
    particle = Mock()
    informer_1 = Mock()
    informer_2 = Mock()

    informer_1.shaman = None
    informer_2.shaman = None

    particle.parent = tribe
    tribe.shaman = particle
    tribe.informers = [informer_1, informer_2]

    assert len(get_external_informers(particle)) == 2


def test_get_external_informers_return_empty_list():
    particle = Mock()
    particle.parent = None

    assert len(get_external_informers(particle)) == 0


def test_get_internal_informers_return_himself():
    tribe = Mock()
    particle = Mock()
    particle.parent = tribe

    tribe.members = [None, None]

    assert get_internal_informers(particle) == [None, None]


def test_get_internal_informers_return_parent_members():
    particle = Mock()
    particle.parent = None

    assert get_internal_informers(particle) == [particle]


def test_move_swarm():
    monkey_patch = MonkeyPatch()
    tribe = Mock()
    particle_1 = Mock()
    particle_2 = Mock()
    mock_move_particle = Mock()

    tribe.members = [particle_1, particle_2]

    monkey_patch.setattr('tribes.move_particle', mock_move_particle)
    move_swarm([tribe], Random(777))
    assert mock_move_particle.call_count == 2


def test_is_swarm_require_adaptation():
    tribes = []
    for _ in range(2):
        tribe = Mock()
        tribe.members = [None, None, None]
        tribe.informers = [None]
        tribes.append(tribe)

    assert is_swarm_require_adaptation(tribes, 2) == False
    assert is_swarm_require_adaptation(tribes, 45) == True


def test_add_informer_to_tribe():
    tribe = Mock()
    informer_1 = Mock()
    informer_2 = Mock()

    tribe.informers = [informer_1]
    informer_2.informers = [tribe]
    add_informer_to_tribe(tribe, informer_2)

    assert len(tribe.informers) == 2


def test_redistribute_links():
    tribe = Mock()
    informer_1 = Mock()
    tribe.informers = [informer_1]
    informer_1.informers = [tribe]

    redistribute_links(tribe, informer_1)
    assert len(tribe.informers) == 0


def test_remove_worst_particle_when_members_count_more_than_one():
    tribe = Mock()
    particle_1 = Mock()
    particle_2 = Mock()

    particle_1.best_solution.error = 1
    particle_2.best_solution.error = 2
    tribe.members = [particle_1, particle_2]

    assert try_remove_worst_particle(tribe) == True
    assert len(tribe.members) == 1


def test_remove_worst_particle_when_members_count_equals_one():
    tribe = Mock()
    informer_1 = Mock()

    tribe.members = [None]
    tribe.best_solution.error = 3
    informer_1.best_solution.error = 1
    tribe.informers = [informer_1]
    informer_1.informers = [tribe]

    assert try_remove_worst_particle(tribe) == True
    assert len(tribe.members) == 0


def test_remove_worst_particle_when_members_count_less_or_equal_zero():
    tribe = Mock()
    tribe.members = []
    assert try_remove_worst_particle(tribe) == False


def test_remove_worst_particle_when_members_count_equals_one_1():
    tribe = Mock()
    informer_1 = Mock()
    tribe.members = [None]

    tribe.informers = [informer_1]
    tribe.best_solution.error = 1
    informer_1.best_solution.error = 3

    assert try_remove_worst_particle(tribe) == False


def test_adapt_swarm():
    tribe_1 = Mock()
    tribe_2 = Mock()
    tribe_3 = Mock()
    particle_1 = Mock()
    particle_2 = Mock()

    tribes = [tribe_1, tribe_2, tribe_3]
    particle_1.best_solution.error = 1
    particle_2.best_solution.error = 2

    tribe_1.members = []
    tribe_2.is_good = True
    tribe_2.members = [particle_1, particle_2]

    tribe_3.members = [particle_1]
    tribe_3.is_good = False
    tribe_3.informers = []

    adapt_swarm(tribes)
    assert len(tribes) == 3
