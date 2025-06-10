import gurobipy as gb
import numpy as np
import types

class Solver:
    def __init__(self, I, S, J, H, L, A1, A2, A4, B, U, V, C, W, Cp, K, E, P, o, f, G, Gp, O, F, T1, T2, a, d, t, n, m, α, β, γ, θ, λ, τ, M):
        self.I = I
        self.S = S
        self.J = J
        self.H = H
        self.L = L
        self.A1 = A1
        self.A2 = A2
        self.A4 = A4
        self.B = B
        self.U = U
        self.V = V
        self.C = C
        self.W = W
        self.Cp = Cp
        self.K = K
        self.E = E
        self.P = P
        self.o = o
        self.f = f
        self.G = G
        self.Gp = Gp
        self.O = O
        self.F = F
        self.T1 = T1
        self.T2 = T2
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
        x = self.estimator.addVars([ (i,s) for i in self.I for s in (self.V[i]+[self.f[i]]) ], vtype=gb.GRB.CONTINUOUS)
        y = self.estimator.addVars([ (i,s) for i in self.I for s in (self.V[i]+[self.o[i]]) ], vtype=gb.GRB.CONTINUOUS)
        δp = self.estimator.addVars([ (i,s) for i in self.I for s in (self.K[i]+[self.f[i]]) ], vtype=gb.GRB.CONTINUOUS)
        δm = self.estimator.addVars([ (i,s) for i in self.I for s in (self.K[i]+[self.f[i]]) ], vtype=gb.GRB.CONTINUOUS)
        p = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s]+self.F[s]) for i2 in (self.G[s]+self.F[s]) if i1<i2 ], vtype=gb.GRB.BINARY)
        q = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.O[s]) if i1<i2 ], vtype=gb.GRB.BINARY)
        r = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.F[s]) if i1!=i2 ], vtype=gb.GRB.BINARY)
        z = self.estimator.addVars([ (s,i) for s in self.S for i in self.G[s] if i not in self.Gp[s] ], vtype=gb.GRB.BINARY)
        h = self.estimator.addVars([ (s,i1,i2) for s in self.S for i1 in self.G[s] for i2 in self.G[s] if ((i1 not in self.Gp[s]) and (i2 not in self.Gp[s]) and (i1!=i2))], vtype=gb.GRB.BINARY)
        w1 = self.estimator.addVars([ (j,i,k) for j in self.A4 for k in [1,2] for i in self.T1[j] ], vtype=gb.GRB.BINARY)
        w2 = self.estimator.addVars([ (j,i,k) for j in self.A4 for k in [1,2] for i in self.T2[j] ], vtype=gb.GRB.BINARY)

        # Departure and arrival constraints
        self.estimator.addConstrs(( y[i,self.o[i]] >= self.d[i,self.o[i]] + self.θ
                                   for i in self.I ))
        self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.d[i,s] - self.a[i,s]
                                   for i in self.I for s in self.V[i] ))
        self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.β
                                   for i in self.I for s in self.C[i] ))
        self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.γ
                                   for i in self.I for s in self.W[i] ))
        self.estimator.addConstrs(( y[i,s] >= x[i,s] + self.α * z[s,i]
                                   for i in self.I for s in set(self.V[i]).intersection(set(self.B)).difference(set(self.C[i])) ))
        self.estimator.addConstrs(( y[i,s] >= self.d[i,s]
                                   for i in self.I for s in self.K[i] ))
        self.estimator.addConstrs(( x[i,self.Pi(i,j,1)] == y[i,self.Pi(i,j,0)] + self.t[i,j]
                                   for i in self.I for j in self.E[i] ))

        # Deviation calculation constraints
        self.estimator.addConstrs(( δp[i,s]-δm[i,s] == x[i,s]-self.a[i,s]
                                   for i in self.I for s in (self.K[i]+[self.f[i]]) ))

        # Arrival and departure order constraints
        self.estimator.addConstrs(( x[i2,s]-x[i1,s] <= self.M * p[s,i1,i2]
                                   for s in self.S for i1 in (self.G[s]+self.F[s]) for i2 in (self.G[s]+self.F[s]) if i1<i2 ))
        self.estimator.addConstrs(( x[i1,s]-x[i2,s] <= self.M * (1-p[s,i1,i2])
                                   for s in self.S for i1 in (self.G[s]+self.F[s]) for i2 in (self.G[s]+self.F[s]) if i1<i2 ))
        self.estimator.addConstrs(( y[i2,s]-y[i1,s] <= self.M * q[s,i1,i2]
                                   for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.O[s]) if i1<i2 ))
        self.estimator.addConstrs(( y[i1,s]-y[i2,s] <= self.M * (1-q[s,i1,i2])
                                   for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.O[s]) if i1<i2 ))
        self.estimator.addConstrs(( x[i2,s]-y[i1,s] <= self.M * r[s,i1,i2]
                                   for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.F[s]) if i1!=i2 ))
        self.estimator.addConstrs(( y[i1,s]-x[i2,s] <= self.M * (1-r[s,i1,i2])
                                   for s in self.S for i1 in (self.G[s]+self.O[s]) for i2 in (self.G[s]+self.F[s]) if i1!=i2 ))

        # Siding and overtake constraints
        self.estimator.addConstrs(( z[s,i] == 0
                                   for s in self.S for i in self.G[s] if ((s not in self.B) and (i not in self.Gp[s]))))
        self.estimator.addConstrs(( h[s,i1,i2] >= (1-p[s,i1,i2]) - r[s,i2,i1] - z[s,i2]
                                   for s in self.S for i1 in self.G[s] for i2 in self.G[s] if ((i1 not in self.Gp[s]) and (i2 not in self.Gp[s]) and (i1<i2)) ))
        self.estimator.addConstrs(( h[s,i1,i2] >= p[s,i2,i1] - r[s,i2,i1] - z[s,i2]
                                   for s in self.S for i1 in self.G[s] for i2 in self.G[s] if ((i1 not in self.Gp[s]) and (i2 not in self.Gp[s]) and (i2<i1)) ))
        self.estimator.addConstrs(( z[s,i1] >= 1 + gb.quicksum(h[s,i1,i2] for i2 in self.G[s] if i2 not in self.Gp[s] and i2 != i1) - self.m[s]
                                   for s in self.S for i1 in self.G[s] if i1 not in self.Gp[s] ))
        self.estimator.addConstrs(( z[s,i1] <=
                                                self.n[s] + self.m[s]
                                                - gb.quicksum(1-p[s,i1,i2] for i2 in self.G[s] if i2 not in self.Gp[s] and i1 < i2)
                                                - gb.quicksum(p[s,i2,i1] for i2 in self.G[s] if i2 not in self.Gp[s] and i2 < i1)
                                                + gb.quicksum(r[s,i2,i1] for i2 in self.G[s] if i2 not in self.Gp[s] and i2 != i1)
                                    for s in self.B for i1 in self.G[s] if i1 not in self.Gp[s] ))
        
        # Single track capacity and headway constraints
        self.estimator.addConstrs(( y[i1,self.Pi(i1,j,0)] >= x[i2,self.Pi(i2,j,0)] - self.M * (1-r[self.Pi(i1,j,1),i2,i1])
                                   for j in self.A1 for i1 in self.T1[j] for i2 in self.T2[j] ))
        self.estimator.addConstrs(( y[i2,self.Pi(i2,j,1)] >= x[i1,self.Pi(i1,j,1)] - self.M * (1-r[self.Pi(i1,j,0),i1,i2])
                                   for j in self.A1 for i1 in self.T1[j] for i2 in self.T2[j] if self.Pi(i2,j,1) != self.f[i2] and self.Pi(i1,j,1) != self.o[i1] ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * q[self.Pi(i1,j,0), i1, i2]
                                   for j in self.A1 for i1 in self.T1[j] for i2 in self.T1[j] if i1 < i2 ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (1-q[self.Pi(i1,j,0), i2, i1])
                                   for j in self.A1 for i1 in self.T1[j] for i2 in self.T1[j] if i2 < i1 ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * q[self.Pi(i1,j,1), i1, i2]
                                   for j in self.A1 for i1 in self.T2[j] for i2 in self.T2[j] if i1 < i2 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (1-q[self.Pi(i1,j,1), i2, i1])
                                   for j in self.A1 for i1 in self.T2[j] for i2 in self.T2[j] if i2 < i1 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] ))
        
        # Double track and headway constraints
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * q[self.Pi(i1,j,0), i1, i2]
                                   for j in self.A2 for i1 in self.T1[j] for i2 in self.T1[j] if i1 < i2 ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (1-q[self.Pi(i1,j,0), i2, i1])
                                   for j in self.A2 for i1 in self.T1[j] for i2 in self.T1[j] if i2 < i1 ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * q[self.Pi(i1,j,1), i1, i2]
                                   for j in self.A2 for i1 in self.T2[j] for i2 in self.T2[j] if i1 < i2 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2] ))
        self.estimator.addConstrs(( y[i1, self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (1-q[self.Pi(i1,j,1), i2, i1])
                                   for j in self.A2 for i1 in self.T2[j] for i2 in self.T2[j] if i2 < i1 and self.Pi(i1,j,1) != self.f[i1] and self.Pi(i2,j,0) != self.o[i2]))
        
        # Quadruple track and headway constraints
        self.estimator.addConstrs(( gb.quicksum(w1[j,i,k] for k in [1,2]) == 1
                                   for j in self.A4 for i in self.T1[j] ))
        self.estimator.addConstrs(( gb.quicksum(w2[j,i,k] for k in [1,2]) == 1
                                   for j in self.A4 for i in self.T2[j] ))
        self.estimator.addConstrs(( y[i1,self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (2 + q[self.Pi(i1,j,0), i1, i2] - w1[j,i1,k] - w1[j,i2,k])
                                    for j in self.A4 for k in [1,2] for i1 in self.T1[j] for i2 in self.T1[j] if i1 < i2 ))
        self.estimator.addConstrs(( y[i1,self.Pi(i1,j,0)] >= x[i2, self.Pi(i2,j,1)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (3 - q[self.Pi(i1,j,0), i2, i1] - w1[j,i1,k] - w1[j,i2,k])
                                    for j in self.A4 for k in [1,2] for i1 in self.T1[j] for i2 in self.T1[j] if i2 < i1 ))
        self.estimator.addConstrs(( y[i1,self.P[j][2]] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (2 + q[self.Pi(i1,j,1), i1, i2] - w2[j,i1,k] - w2[j,i2,k])
                                    for j in self.A4 for k in [1,2] for i1 in self.T2[j] for i2 in self.T2[j] if i1 < i2 ))
        self.estimator.addConstrs(( y[i1,self.Pi(i1,j,1)] >= x[i2, self.Pi(i2,j,0)] + self.tau(self.t[i1,j],self.t[i2,j]) - min(self.t[i1,j], self.t[i2,j])
                                    - self.M * (3 - q[self.Pi(i1,j,1), i2, i1] - w2[j,i1,k] - w2[j,i2,k])
                                    for j in self.A4 for k in [1,2] for i1 in self.T2[j] for i2 in self.T2[j] if i2 < i1 ))
        
        # Drop off/Pick up capacity constraint for non-yard stations
        self.estimator.addConstrs(( x[i1,s] >= y[i2,s] - self.M * p[s,i1,i2]
                                   for s in self.U for i1 in self.Gp[s] for i2 in self.Gp[s] if i1 < i2 ))
        self.estimator.addConstrs(( x[i1,s] >= y[i2,s] - self.M * (1-p[s,i2,i1])
                                   for s in self.U for i1 in self.Gp[s] for i2 in self.Gp[s] if i2 < i1 ))
        
        # Objective function
        self.estimator.setObjective(
            ( self.λ * gb.quicksum(δp[i,s] for i in self.H for s in (self.K[i]+[self.f[i]]))
            + gb.quicksum(δp[i,s] for i in self.L for s in (self.K[i]+[self.f[i]])) ),
            gb.GRB.MINIMIZE
        )

        # Run
        self.estimator.optimize()

        for i in self.I:
            for s in self.V[i]+[self.f[i]]:
                print(f"x[{i},{s}]={x[i,s].X}")
        print("---")
        for i in self.I:
            for s in self.V[i]+[self.o[i]]:
                print(f"y[{i},{s}]={y[i,s].X}")
