def producer():
    # 生产 4 个数据
    for i in range(4):
        sys_P("empty")  # 等待空槽位
        sys_P("mutex")  # 进入临界区

        heap.buffer.append(i)
        sys_write(f"Produced {i}\n")

        sys_V("mutex")  # 离开临界区
        sys_V("full")  # 增加满槽位计数


def consumer():
    # 消费 4 个数据
    for i in range(4):
        sys_P("full")  # 等待满槽位
        sys_P("mutex")  # 进入临界区

        item = heap.buffer.pop(0)
        sys_write(f"Consumed {item}\n")

        sys_V("mutex")  # 离开临界区
        sys_V("empty")  # 增加空槽位计数


def main():
    # 初始化信号量
    sys_sem_init("mutex", 1)  # 互斥锁
    sys_sem_init("empty", 2)  # 缓冲区大小为 1
    sys_sem_init("full", 0)  # 初始满槽位为 0

    # 初始化共享缓冲区
    heap.buffer = []

    # 创建生产者和消费者线程（共享堆内存）
    sys_spawn(producer)
    sys_spawn(consumer)
