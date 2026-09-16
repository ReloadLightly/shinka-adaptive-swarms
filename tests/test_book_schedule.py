"""Pure numerical schedule contract; no full simulator executions."""
from pathlib import Path
import pytest

from adaptive_swarms.book_schedule import (BookScheduleError, inspect_schedule_source,
                                          load_schedule, validated_count)


@pytest.mark.parametrize('value',[0,1,2,3,4,5])
def test_exact_integer_counts(value):
    assert validated_count(value) == value


@pytest.mark.parametrize('value',[-1,6,True,False,1.0,float('nan'),float('inf'),'4',None])
def test_invalid_count_fails(value):
    with pytest.raises(BookScheduleError):
        validated_count(value)


@pytest.mark.parametrize('source',[
    'import math\ndef choose_temporary_quantum_count(obs):\n return min(5, int(math.sqrt(obs["x"])))\n',
    'def choose_temporary_quantum_count(obs):\n import math\n return min(5, int(math.sqrt(obs["x"])))\n',
    'def choose_temporary_quantum_count(obs):\n from math import sqrt as root\n return min(5, int(root(obs["x"])))\n',
    'import math as m\ndef choose_temporary_quantum_count(obs):\n return min(5, int(m.sqrt(obs["x"])))\n',
    'def helper(x, y=0):\n return x+y\ndef choose_temporary_quantum_count(obs):\n return min(5, int(sum(helper(a,b) for a,b in zip((2,),(2,)))))\n',
    'COUNT=4\ndef choose_temporary_quantum_count(obs):\n return COUNT\n',
])
def test_documented_math_and_numerical_builtins_work_at_both_scopes(tmp_path,source):
    path=tmp_path/'candidate.py';path.write_text(source)
    assert load_schedule(path)({'x':16})==4


@pytest.mark.parametrize('source',[
    'import os\ndef choose_temporary_quantum_count(obs):\n return 0\n',
    'def choose_temporary_quantum_count(obs):\n import random\n return random.randrange(6)\n',
    'def choose_temporary_quantum_count(obs):\n return int(open("data").read())\n',
    'def choose_temporary_quantum_count(obs):\n return eval("4")\n',
    'def choose_temporary_quantum_count(obs):\n return obs.__class__\n',
    'VALUE=0\ndef choose_temporary_quantum_count(obs):\n global VALUE\n VALUE+=1\n return VALUE\n',
])
def test_external_access_and_persistent_state_rejected_before_numerical_work(tmp_path,source):
    path=tmp_path/'candidate.py';path.write_text(source)
    with pytest.raises(BookScheduleError) as failure:
        load_schedule(path)
    assert failure.value.objective_queries==0


def test_snapshot_is_read_only_and_invalid_return_is_not_successful_fallback(tmp_path):
    path=tmp_path/'candidate.py'
    path.write_text('def choose_temporary_quantum_count(obs):\n obs["x"]=4\n return 4\n')
    with pytest.raises(TypeError):
        load_schedule(path)({'x':16})
    path.write_text('def choose_temporary_quantum_count(obs):\n return 4.0\n')
    with pytest.raises(BookScheduleError):
        load_schedule(path)({'x':16})


def test_exact_initial_published_schedule():
    root=Path(__file__).resolve().parents[1]
    schedule=load_schedule(root/'tasks/book_mpso_schedule_v1/initial.py')
    assert schedule({'change_detected':True})==5
    assert schedule({'change_detected':False})==0
