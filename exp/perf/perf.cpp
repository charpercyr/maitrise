
#include <chrono>
#include <cmath>
#include <iostream>
#include <fstream>
#include <string>

using namespace std;

#define CLOBBER() asm volatile("":::"memory")

using duration = chrono::duration<double, nano>;

uint64_t arg_b = 5;
uint64_t arg_e = 123;
uint64_t arg_m = 1030;

extern "C" [[gnu::noinline]]
uint64_t powmod(uint64_t b, uint64_t e, uint64_t m)
{
    uint64_t c = 1;
    for(size_t i = 0; i < e; ++i)
    {
        c = (c * b) % m;
        CLOBBER();
    }
    return c;
}

duration do_run(size_t n_iter)
{
    auto start = chrono::steady_clock::now();
    for(size_t i = 0; i < n_iter; ++i)
    {
        powmod(arg_b, arg_e, arg_m);
    }
    auto end = chrono::steady_clock::now();
    return chrono::duration_cast<duration>(end - start);
}

void show_usage(char* argv0, int e)
{
    cout << "Usage: " << argv0 << " <out_file> [runs] [iter/run]\n";
    exit(e);
}

int main(int argc, char** argv)
{
    size_t n_runs = 100;
    size_t n_iter = 50000;
    ofstream out;
    if(argc == 1)
        show_usage(argv[0], 0);
    if(argc >= 2)
    {
        out = ofstream{argv[1], ios::out | ios::trunc};
        if(!out)
        {
            cerr << "Could not open file " << argv[1] << " for writing\n";
            exit(1);
        }
    }
    if(argc >= 3)
        n_runs = atoi(argv[2]);
    if(argc >= 4)
        n_iter = atoi(argv[3]);

    if(n_runs == 0 || n_iter == 0)
    {
        show_usage(argv[0], 1);
    }

    getchar();
    out << "Runs," << n_runs << "\n";
    out << "Iterations," << n_iter << "\n";
    out << "Run,Time (ns)\n";

    double mean = 0;
    double stddev = 0;
    for(size_t i = 0; i < n_runs; ++i)
    {
        auto dur = do_run(n_iter);
        dur /= n_iter;
        mean += dur.count();
        stddev += dur.count()*dur.count();
        out << i << "," << dur.count() << "\n";
    }
    mean /= n_runs;
    stddev /= n_runs;
    stddev = sqrt(stddev - mean*mean);
    cout << "Iterations: " << n_runs << " x " << n_iter << "\n";
    cout << "mean:       " << mean << " ns\n";
    cout << "stddev:     " << stddev << " ns\n";
    return 0;
}