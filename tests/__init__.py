import os

# Must be set before numpy is imported: multi-threaded BLAS makes
# the twin's many small array operations far slower, not faster.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")
