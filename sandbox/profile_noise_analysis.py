import pstats
p = pstats.Stats('profNoise.prof')
p.sort_stats('time', 'cum').print_stats(0.8, 'init')