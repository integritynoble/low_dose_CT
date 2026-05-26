import os
import sys

# make `import pwm_ldct_prep` resolve to the package under pipelines/ regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
