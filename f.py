
for n in range(0,7):
  f = lambda myself, n: 1 if n==0 or n==1 else myself(myself, n-1) + myself(myself, n-2)
  print(f(f, n))

