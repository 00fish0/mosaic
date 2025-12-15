# MOSAIC Operating System Model and Checker

This is the artifact for Paper #202 of USENIX ATC'23 "The Hitchhiker’s Guide to Operating Systems". (Cherry-picked from the backend of my [course homepage](http://jyywiki.cn/OS/2023/build/lect4.ipynb).)

- [mosaic.py](mosaic.py) - The model checker (zero dependency; self-documented)
- [vis/](vis/) - The visualization script of an interactive state space explorer
- [examples/](examples/) - The code examples evaluated in the paper

## The Operating System Model

MOSAIC supports simple applications with "system calls". The program entry is `main()`:

```python
def main():
    pid = sys_fork()
    sys_sched()  # non-deterministic context switch
    if pid == 0:
        sys_write('World\n')
    else:
        sys_write('Hello\n')
```

MOSAIC can interpret these system calls, or model-check it:

    python3 mosaic.py --run foo.py
    python3 mosaic.py --check bar.py

A JSON file (state transition graph) will be printed to stdout.
The output (state transition graph) can be piped to another tool, e.g., a
visualization tool:

```bash
# quick and dirty check
python3 mosaic.py --check examples/hello.py | grep stdout | sort | uniq
```

```bash
# interactive state explorer
python3 mosaic.py --check examples/hello.py | python3 -m vis
```

![](vis/demo.png)

## Modeled System Calls

System Call         | Behavior
--------------------|-----------------------------------------------
`sys_fork()`        | create current thread's heap and context clone
`sys_spawn(f, xs)`  | spawn a heap-sharing thread executing `f(xs)`
`sys_write(xs)`     | write string `xs` to a shared console
`sys_bread(k)`      | return the value of block id `k`
`sys_bwrite(k, v)`  | write block `k` with value `v`
`sys_sync()`        | persist all outstanding block writes
`sys_sched()`       | perform a non-deterministic context switch
`sys_choose(xs)`    | return a non-deterministic choice in `xs`
`sys_crash()`       | perform a non-deterministic crash
`sys_sem_init(name, value)` | initialize a semaphore with initial value
`sys_P(name)`       | wait (P operation) on a semaphore
`sys_V(name)`       | signal (V operation) on a semaphore

Limitation: system calls are implemented by `yield`. To keep the model checker minimal, one cannot perform system call in a function. (This is not a fundamental limitation and will be addressed in the future.)

## Using Semaphores: Producer-Consumer Example

MOSAIC now supports semaphore synchronization primitives (P and V operations) for modeling concurrent systems. Here's how to use them to implement a classic producer-consumer problem:

### Basic Semaphore Operations

```python
# Initialize a semaphore with a name and initial value
sys_sem_init('mutex', 1)     # Binary semaphore for mutual exclusion
sys_sem_init('empty', 5)     # Counting semaphore: 5 empty slots
sys_sem_init('full', 0)      # Counting semaphore: 0 filled slots

# P operation (wait/down): decrements semaphore, blocks if value becomes negative
sys_P('mutex')               # Acquire lock

# V operation (signal/up): increments semaphore, wakes a waiting thread if any
sys_V('mutex')               # Release lock
```

### Producer-Consumer Implementation

```python
def producer():
    for i in range(4):
        sys_P("empty")       # Wait for empty slot
        sys_P("mutex")       # Enter critical section
        
        heap.buffer.append(i)
        sys_write(f"Produced {i}\n")
        
        sys_V("mutex")       # Leave critical section
        sys_V("full")        # Signal that buffer has data

def consumer():
    for i in range(4):
        sys_P("full")        # Wait for data
        sys_P("mutex")       # Enter critical section
        
        item = heap.buffer.pop(0)
        sys_write(f"Consumed {item}\n")
        
        sys_V("mutex")       # Leave critical section
        sys_V("empty")       # Signal that buffer has space

def main():
    # Initialize semaphores
    sys_sem_init("mutex", 1)  # Mutual exclusion lock
    sys_sem_init("empty", 2)  # Buffer capacity = 2
    sys_sem_init("full", 0)   # Initially no data
    
    # Initialize shared buffer
    heap.buffer = []
    
    # Spawn producer and consumer threads (sharing heap)
    sys_spawn(producer)
    sys_spawn(consumer)
```

Run the example:

```bash
# Check all possible execution paths
python3 mosaic.py --check examples/producer_consumer.py | grep stdout | sort | uniq

# Interactive state space explorer
python3 mosaic.py --check examples/producer_consumer.py | python3 -m vis > index.html
```

With buffer size 2, you'll see various interleavings like:
- `P0 C0 P1 C1 P2 C2 P3 C3` (strict alternation)
- `P0 P1 C0 C1 P2 P3 C2 C3` (batch produce then consume)
- `P0 C0 P1 P2 C1 C2 P3 C3` (mixed patterns)

The model checker explores all possible thread scheduling decisions, especially at semaphore operations where thread wake-ups can trigger different execution paths.

## Reproducing Results

```bash
python3 examples/_reproduce.py
```

Similar results in Table 2 are expected. Tested on: Python 3.10.9 (macOS Ventura), Python 3.11.2 (Ubuntu 22.04)
