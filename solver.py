import gurobipy as gb
import types

class Solver:
  def __init__(self, I, S, J, H, L, A1, A2, A4, B, U, V, C, W, K, E, P, o, f, G, Gp, O, F, T1, T2, a, d, t, n, m, α, β, γ, θ, λ, τ, M):
    self.I = set(I)
    self.S = set(S)
    self.J = set(J)
    self.H = set(H)
    self.L = set(L)
    self.A1 = set(A1)
    self.A2 = set(A2)
    self.A4 = set(A4)
    self.B = set(B)
    self.U = set(U)
    self.V = [set(lista) for lista in V]
    self.C = [set(lista) for lista in C]
    self.W = [set(lista) for lista in W]   
    self.K = [set(lista) for lista in K]
    self.E = [set(lista) for lista in E]   
    self.P = P
    self.o = o
    self.f = f
    self.G = [set(lista) for lista in G]
    self.Gp = [set(lista) for lista in Gp]
    self.O = [set(lista) for lista in O]
    self.F = [set(lista) for lista in F]
    self.T1 = [set(lista) for lista in T1]   
    self.T2 = [set(lista) for lista in T2]   
    self.a = a
    self.d = d
    self.t = t
    self.n = n
    self.m = m
    self.α = α
    self.β = β
    self.γ = γ
    self.θ = θ
    self.λ = λ
    self.τ = τ
    self.M = M
    self.estimator = gb.Model()

  def tau(self, a, b):
    if isinstance(self.τ, types.LambdaType) and self.τ.__name__ == "<lambda>":
      return self.τ(a,b)
    else:
      return self.τ
    
  def Pi(self, i, j, k):
    if i in self.T1[j]:
      k = (~k)&1
    return self.P[j][k]
      

  def solve(self):
    # Decision Variables
    print("Adding decision variables...")
    x = self.estimator.addVars([ (i,s) for i in self.I for s in (self.V[i] | {self.f[i]}) ],
                   vtype=gb.GRB.CONTINUOUS, name='x')
    y = self.estimator.addVars([ (i,s) for i in self.I for s in (self.V[i] | {self.o[i]}) ],
                   vtype=gb.GRB.CONTINUOUS, name='y')
    δp = self.estimator.addVars([ (i,s) for i in self.I for s in (self.K[i] | {self.f[i]}) ],
                  vtype=gb.GRB.CONTINUOUS, name='dp')
    δm = self.estimator.addVars([ (i,s) for i in self.I for s in (self.K[i] | {self.f[i]}) ],
                  vtype=gb.GRB.CONTINUOUS, name='dm')
    p = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s] | self.F[s]) for i2 in (self.G[s] | self.F[s]) if i1<i2 ],
                   vtype=gb.GRB.BINARY, name='p')
    q = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.O[s]) if i1<i2 ],
                   vtype=gb.GRB.BINARY, name='q')
    r = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.F[s]) if i1!=i2 ],
                   vtype=gb.GRB.BINARY, name='r')
    z = self.estimator.addVars([ (s,i) for s in self.S for i in self.G[s] if i not in self.Gp[s] ],
                   vtype=gb.GRB.BINARY, name='z')
    h = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s] - self.Gp[s]) for i2 in (self.G[s] - self.Gp[s]) if i1!=i2],
                   vtype=gb.GRB.BINARY, name='h')
    w1 = self.estimator.addVars([ (j,i,k) for j in self.A4 for k in [1,2] for i in self.T1[j] ],
                  vtype=gb.GRB.BINARY, name='w1')
    w2 = self.estimator.addVars([ (j,i,k) for j in self.A4 for k in [1,2] for i in self.T2[j] ],
                  vtype=gb.GRB.BINARY, name='w2')
    
    self._vars = {'x': x, 'y': y, 'dp': δp, 'dm': δm, 'p': p, 'q': q, 'r': r, 'z': z, 'h': h, 'w1': w1, 'w2': w2}
    self._x = x

    # Departure and arrival constraints
    print("Adding departure and arrival constraints...")
    # 1
    self.estimator.addConstrs(( y[i,self.o[i]] >= self.d[i,self.o[i]] + self.θ
                   for i in self.I ))
    # 2
    self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.d[i,s] - self.a[i,s]
                   for i in self.I for s in self.V[i] ))
    # 3
    self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.β
                   for i in self.I for s in self.C[i] ))
    # 4
    self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.γ
                   for i in self.I for s in (self.W[i] - {self.o[i]}) ))
    # 5
    self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.α * z[s,i]
                   for i in self.I for s in ((self.V[i] & self.B) - self.C[i] )) )
    # 6
    self.estimator.addConstrs(( y[i,s] >= self.d[i,s]
                   for i in self.I for s in self.K[i] ))
    # 7
    self.estimator.addConstrs(( x[i,self.Pi(i,j,1)] == y[i,self.Pi(i,j,0)] + self.t[i,j]
                   for i in self.I for j in self.E[i] ))

    # Deviation calculation constraints
    print("Adding deviation calculation constraints...")
    # 8
    self.estimator.addConstrs(( δp[i,s]-δm[i,s] == x[i,s]-self.a[i,s]
                   for i in self.I for s in (self.K[i] | {self.f[i]}) ))

    # Arrival and departure order constraints
    print("Adding arrival and departure order constraints...")
    # 9
    self.estimator.addConstrs(( x[i2,s]-x[i1,s] <= self.M * p[s,i1,i2]
                   for s in self.S for i1 in (self.G[s] | self.F[s]) for i2 in (self.G[s] | self.F[s]) if i1<i2 ))
    # 10
    self.estimator.addConstrs(( x[i1,s]-x[i2,s] <= self.M * (1-p[s,i1,i2])
                   for s in self.S for i1 in (self.G[s] | self.F[s]) for i2 in (self.G[s] | self.F[s]) if i1<i2 ))
    # 11
    self.estimator.addConstrs(( y[i2,s]-y[i1,s] <= self.M * q[s,i1,i2]
                   for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.O[s]) if i1<i2 ))
    # 12
    self.estimator.addConstrs(( y[i1,s]-y[i2,s] <= self.M * (1-q[s,i1,i2])
                   for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.O[s]) if i1<i2 ))
    # 13
    self.estimator.addConstrs(( x[i2,s]-y[i1,s] <= self.M * r[s,i1,i2]
                   for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.F[s]) if i1!=i2 ))
    # 14
    self.estimator.addConstrs(( y[i1,s]-x[i2,s] <= self.M * (1-r[s,i1,i2])
                   for s in self.S for i1 in (self.G[s] | self.O[s]) for i2 in (self.G[s] | self.F[s]) if i1!=i2 ))

    # Siding and overtake constraints
    print("Adding siding and overtake constraints...")
    # 15
    self.estimator.addConstrs(( z[s,i] == 0
                   for s in (self.S - self.B) for i in (self.G[s] - self.Gp[s]) ))

    # Quadruple track and headway constraints
    print("Adding quadruple track capacity and headway constraints...")
    # 30
    self.estimator.addConstrs(( gb.quicksum(w1[j,i,k] for k in [1,2]) == 1
                   for j in self.A4 for i in self.T1[j] ))
    # 31
    self.estimator.addConstrs(( gb.quicksum(w2[j,i,k] for k in [1,2]) == 1
                   for j in self.A4 for i in self.T2[j] ))

    # Objective function
    print("Adding objective function...")
    self.estimator.setObjective(
      ( self.λ * gb.quicksum(δp[i,s] for i in self.H for s in (self.K[i] | {self.f[i]}))
      + gb.quicksum(δp[i,s] for i in self.L for s in (self.K[i] | {self.f[i]})) ),
      gb.GRB.MINIMIZE
    )

    # Parameters
    self.estimator.Params.LazyConstraints = 1
    self.estimator.Params.MIPGap = 0.01
    self.estimator.Params.Method = 1
    #self.estimator.Params.MIPFocus = 1
    # self.estimator.Params.ConcurrentMethod = 3
    # self.estimator.Params.SoftMemLimit = 24
    #self.estimator.Params.NodefileStart = 0.1
    #self.estimator.Params.Threads = 4

    # Run
    print("Starting...")
    self.estimator.optimize(self.callback)

  def callback(self, model:gb.Model, where):
    if where == gb.GRB.Callback.MIPSOL:
      """vars = model.cbGetSolution(self._x)
      print(vars)"""
      x = model.cbGetSolution(self._vars['x'])
      y = model.cbGetSolution(self._vars['y'])
      p = model.cbGetSolution(self._vars['p'])
      q = model.cbGetSolution(self._vars['q'])
      r = model.cbGetSolution(self._vars['r'])
      z = model.cbGetSolution(self._vars['z'])
      h = model.cbGetSolution(self._vars['h'])
      w1 = model.cbGetSolution(self._vars['w1'])
      w2 = model.cbGetSolution(self._vars['w2'])
      # 16
      for s in self.S:
        for i1 in (self.G[s] - self.Gp[s]):
          for i2 in (self.G[s] - self.Gp[s]):
            if i1 < i2:
              if not h[s, i1, i2] >= (1-p[s,i1,i2]) - r[s,i2,i1] - z[s,i2]:
                model.cbLazy(self._vars['h'][s,i1,i2] >= (1-self._vars['p'][s,i1,i2]) - self._vars['r'][s,i2,i1] - self._vars['z'][s,i2])
      # 17
      for s in self.S:
        for i1 in (self.G[s] - self.Gp[s]):
          for i2 in (self.G[s] - self.Gp[s]):
            if i2 < i1:
              if not h[s,i1,i2] >= p[s,i2,i1] - r[s,i2,i1] - z[s,i2]:
                model.cbLazy(self._vars['h'][s,i1,i2] >= self._vars['p'][s,i2,i1] - self._vars['r'][s,i2,i1] - self._vars['z'][s,i2])
      # 18
      for s in self.S:
        for i1 in (self.G[s] - self.Gp[s]):
          if not z[s,i1] >= 1 + gb.quicksum(h[s,i1,i2] for i2 in (self.G[s] - self.Gp[s]) if i2 != i1).getValue() - self.m[s]:
            model.cbLazy(self._vars['z'][s,i1] >= 1 + gb.quicksum(self._vars['h'][s,i1,i2] for i2 in (self.G[s] - self.Gp[s]) if i2 != i1) - self.m[s])
      # 19
      for s in self.B:
        for i1 in (self.G[s] - self.Gp[s]):
          if not (z[s,i1] <= self.n[s] + self.m[s]
                      - gb.quicksum(1-p[s,i1,i2] for i2 in (self.G[s] - self.Gp[s]) if i1 < i2).getValue()
                      - gb.quicksum(p[s,i2,i1] for i2 in (self.G[s] - self.Gp[s]) if i2 < i1).getValue()
                      + gb.quicksum(r[s,i2,i1] for i2 in (self.G[s] - self.Gp[s]) if i2 != i1).getValue()):
            model.cbLazy( self._vars['z'][s,i1] <= self.n[s] + self.m[s]
                          - gb.quicksum(1-self._vars['p'][s,i1,i2] for i2 in (self.G[s] - self.Gp[s]) if i1 < i2)
                          - gb.quicksum(self._vars['p'][s,i2,i1] for i2 in (self.G[s] - self.Gp[s]) if i2 < i1)
                          + gb.quicksum(self._vars['r'][s,i2,i1] for i2 in (self.G[s] - self.Gp[s]) if i2 != i1))
      # 20
      for j in self.A1:
        for i1 in self.T1[j]:
          for i2 in self.T2[j]:
            if self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2, j, 0) != self.o[i2]:
              if not y[i1,self.Pi(i1,j,0)] >= x[i2,self.Pi(i2,j,0)] - self.M * (1-r[self.Pi(i1,j,1),i2,i1]):
                model.cbLazy(self._vars['y'][i1,self.Pi(i1,j,0)] >= 
                             self._vars['x'][i2,self.Pi(i2,j,0)] - self.M * (1-self._vars['r'][self.Pi(i1,j,1),i2,i1]))
      # 21
      for j in self.A1:
        for i1 in self.T1[j]:
          for i2 in self.T2[j]:
            if self.Pi(i2,j,1) != self.f[i2] and self.Pi(i1,j,1) != self.o[i1]:
              if not y[i2,self.Pi(i2,j,1)] >= x[i1,self.Pi(i1,j,1)] - self.M * (1-r[self.Pi(i1,j,0),i1,i2]):
                model.cbLazy(self._vars['y'][i2,self.Pi(i2,j,1)] >=
                              self._vars['x'][i1,self.Pi(i1,j,1)] - self.M * (1-self._vars['r'][self.Pi(i1,j,0),i1,i2]))
      # 22 - to guarantee the existance of x, y, and q the considered stations must be checked against the origin and destinations
      for j in self.A1:
        for i1 in self.T1[j]:
          for i2 in self.T1[j]:
            if i1 < i2 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * q[self.Pi(i1,j,0), i1, i2]):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                                      + self.tau(self.t[i1,j],self.t[i2,j])
                                                                      - min(self.t[i1,j], self.t[i2,j])
                                                                      - self.M * self._vars['q'][self.Pi(i1,j,0), i1, i2])
      # 23
      for j in self.A1:
        for i1 in self.T1[j]:
          for i2 in self.T1[j]:
            if i2 < i1 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * (1-q[self.Pi(i1,j,0), i2, i1])):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * (1-self._vars['q'][self.Pi(i1,j,0), i2, i1]))
      # 24
      for j in self.A1:
        for i1 in self.T2[j]:
          for i2 in self.T2[j]:
            if i1 < i2 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * q[self.Pi(i1,j,1), i1, i2]):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * self._vars['q'][self.Pi(i1,j,1), i1, i2])
      # 25
      for j in self.A1:
        for i1 in self.T2[j]:
          for i2 in self.T2[j]:
            if i2 < i1 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * (1-q[self.Pi(i1,j,1), i2, i1])):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * (1-self._vars['q'][self.Pi(i1,j,1), i2, i1]))
      # 26
      for j in self.A2:
        for i1 in self.T1[j]:
          for i2 in self.T1[j]:
            if i1 < i2 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * q[self.Pi(i1,j,0), i1, i2]):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * self._vars['q'][self.Pi(i1,j,0), i1, i2])
      # 27
      for j in self.A2:
        for i1 in self.T1[j]:
          for i2 in self.T1[j]:
            if i2 < i1 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * (1-q[self.Pi(i1,j,0), i2, i1])):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * (1-self._vars['q'][self.Pi(i1,j,0), i2, i1]))
      # 28
      for j in self.A2:
        for i1 in self.T2[j]:
          for i2 in self.T2[j]:
            if i1 < i2 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * q[self.Pi(i1,j,1), i1, i2]):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * self._vars['q'][self.Pi(i1,j,1), i1, i2])
      # 29
      for j in self.A2:
        for i1 in self.T2[j]:
          for i2 in self.T2[j]:
            if i2 < i1 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
              if not (y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)]
                                                + self.tau(self.t[i1,j],self.t[i2,j])
                                                - min(self.t[i1,j], self.t[i2,j])
                                                - self.M * (1-q[self.Pi(i1,j,1), i2, i1])):
                model.cbLazy(self._vars['y'][i1, self.Pi(i1,j,1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                                    - min(self.t[i1,j], self.t[i2,j])
                                                                    - self.M * (1-self._vars['q'][self.Pi(i1,j,1), i2, i1]))
      # 32
      for j in self.A4:
        for k in [1,2]:
          for i1 in self.T1[j]:
            for i2 in self.T1[j]:
              if i1 < i2 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
                if not (y[i1,self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                  + self.tau(self.t[i1,j],self.t[i2,j])
                                                  - min(self.t[i1,j], self.t[i2,j])
                                                  - self.M * (2 + q[self.Pi(i1,j,0), i1, i2] - w1[j,i1,k] - w1[j,i2,k])):
                  model.cbLazy(self._vars['y'][i1,self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                          + self.tau(self.t[i1,j],self.t[i2,j])
                                                          - min(self.t[i1,j], self.t[i2,j])
                                                          - self.M * (2 + self._vars['q'][self.Pi(i1,j,0), i1, i2]
                                                                      - self._vars['w1'][j,i1,k]
                                                                      - self._vars['w1'][j,i2,k]))
      # 33
      for j in self.A4:
        for k in [1,2]:
          for i1 in self.T1[j]:
            for i2 in self.T1[j]:
              if i2 < i1 and self.Pi(i1,j,0) != self.f[i1] and self.Pi(i2,j,1) != self.o[i2] and self.Pi(i1,j,0) != self.f[i2]:
                if not (y[i1,self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)]
                                                  + self.tau(self.t[i1,j],self.t[i2,j])
                                                  - min(self.t[i1,j], self.t[i2,j])
                                                  - self.M * (3 - q[self.Pi(i1,j,0), i2, i1] - w1[j,i1,k] - w1[j,i2,k])):
                  model.cbLazy(self._vars['y'][i1,self.Pi(i1,j,0)] >= self._vars['x'][i2, self.Pi(i2,j,1)]
                                                          + self.tau(self.t[i1,j],self.t[i2,j])
                                                          - min(self.t[i1,j], self.t[i2,j])
                                                          - self.M * (3 - self._vars['q'][self.Pi(i1,j,0), i2, i1]
                                                                      - self._vars['w1'][j,i1,k]
                                                                      - self._vars['w1'][j,i2,k]))
      # 34
      for j in self.A4:
        for k in [1,2]:
          for i1 in self.T2[j]:
            for i2 in self.T2[j]:
              if i1 < i2 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
                if not (y[i1,self.Pi(i1, j, 1)] >= x[i2, self.Pi(i2,j,0)]
                                                    + self.tau(self.t[i1,j],self.t[i2,j])
                                                    - min(self.t[i1,j], self.t[i2,j])
                                                    - self.M * (2 + q[self.Pi(i1,j,1), i1, i2] - w2[j,i1,k] - w2[j,i2,k])):
                  model.cbLazy(self._vars['y'][i1,self.Pi(i1, j, 1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                            + self.tau(self.t[i1,j],self.t[i2,j])
                                                            - min(self.t[i1,j], self.t[i2,j])
                                                            - self.M * (2 + self._vars['q'][self.Pi(i1,j,1), i1, i2]
                                                                        - self._vars['w2'][j,i1,k]
                                                                        - self._vars['w2'][j,i2,k]))
      # 35
      for j in self.A4:
        for k in [1,2]:
          for i1 in self.T2[j]:
            for i2 in self.T2[j]:
              if i2 < i1 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] and self.Pi(i1,j,1) != self.f[i2]:
                if not (y[i1,self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)]
                                                  + self.tau(self.t[i1,j],self.t[i2,j])
                                                  - min(self.t[i1,j], self.t[i2,j])
                                                  - self.M * (3 - q[self.Pi(i1,j,1), i2, i1] - w2[j,i1,k] - w2[j,i2,k])):
                  model.cbLazy(self._vars['y'][i1,self.Pi(i1,j,1)] >= self._vars['x'][i2, self.Pi(i2,j,0)]
                                                          + self.tau(self.t[i1,j],self.t[i2,j])
                                                          - min(self.t[i1,j], self.t[i2,j])
                                                          - self.M * (3 - self._vars['q'][self.Pi(i1,j,1), i2, i1]
                                                                      - self._vars['w2'][j,i1,k]
                                                                      - self._vars['w2'][j,i2,k]))
      # 36
      for s in self.U:
        for i1 in self.Gp[s]:
          for i2 in self.Gp[s]:
            if i1 < i2 and s != self.o[i1] and s != self.f[i2]:
              if not (x[i1,s] >= y[i2,s] - self.M * p[s,i1,i2]):
                model.cbLazy(self._vars['x'][i1,s] >= self._vars['y'][i2,s] - self.M * self._vars['p'][s,i1,i2])
      # 37
      for s in self.U:
        for i1 in self.Gp[s]:
          for i2 in self.Gp[s]:
            if i2 < i1 and s != self.o[i1] and s != self.f[i2]:
              if not (x[i1,s] >= y[i2,s] - self.M * (1-p[s,i2,i1])):
                model.cbLazy(self._vars['x'][i1,s] >= self._vars['y'][i2,s] - self.M * (1-self._vars['p'][s,i2,i1]))
