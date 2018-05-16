# Abstract
# Introduction
## Related Work
# Algorithms
## Tracepoint creation
1. Analyzing replaced instructions
2. Finding free memory
3. Instruction patching
4. Atomic placement
    - 3 steps 32-bit
    - 1 step 64-bit
## Tracepoint execution
1. Jump pad
2. Save state
3. Refcount
4. Trace
5. Refcount
6. Restore state
7. Out-of-line
8. Jump back
## Tracepoint deletion
1. Atomic removal
    - 3 steps 32-bit
    - 1 step 64-bit
2. Delayed deletion
    - Refcount
    - IP check
# Results
## Experimental setup
## Performance
## Memory Usage
## Availability
# Conclusion