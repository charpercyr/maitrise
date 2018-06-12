
#include <chrono>
#include <iostream>
#include <string>
#include <sstream>
#include <future>
#include <vector>

using namespace std;

#define CLOBBER() asm volatile("":::"memory")

using duration = chrono::nanoseconds;

extern "C" [[gnu::noinline]] uint64_t powmod(uint64_t b, uint64_t e, uint64_t m)
{
    uint64_t c = 1;
    for(size_t i = 0; i < e; ++i)
    {
        c = (c * b) % m;
        CLOBBER();
    }
    return c;
}

[[noreturn]]
void show_usage(char* prog, int ret)
{
    cout << prog << " <# threads> <# iters> <b> <e> <m>\n";
    exit(ret);
}

duration do_run(shared_future<void> barrier, uint64_t iters, uint64_t b, uint64_t e, uint64_t m)
{
    barrier.wait();

    auto start = chrono::steady_clock::now();
    for(size_t i = 0; i < iters; ++i)
    {
        powmod(b, e, m);
    }
    auto end = chrono::steady_clock::now();
    return chrono::duration_cast<chrono::nanoseconds>(end - start);
}

int main(int argc, char** argv)
{
    if (argc < 6)
        show_usage(argv[0], argc == 1 ? 0 : 1);

    size_t threads, iters, b, e, m;

    istringstream{argv[1]} >> threads;
    istringstream{argv[2]} >> iters;
    istringstream{argv[3]} >> b;
    istringstream{argv[4]} >> e;
    istringstream{argv[5]} >> m;

    if(threads == 0 || iters == 0 || b == 0 || e == 0 || m == 0)
        exit(1);

    while(getchar() != EOF);

    duration total{0};

    promise<void> promise;
    shared_future<void> barrier{promise.get_future()};
    vector<future<duration>> results(threads);

    for(auto& r : results)
        r = async(do_run, barrier, iters, b, e, m);
    
    promise.set_value();
    
    for(auto& r : results)
        total += r.get();
    
    cout << total.count() << "\n";

    return 0;
}