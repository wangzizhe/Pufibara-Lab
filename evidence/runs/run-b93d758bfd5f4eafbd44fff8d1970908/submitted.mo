model Cooling
  parameter Real C = 1000 "Thermal capacity J/K";
  parameter Real G = 10 "Thermal conductance W/K";
  parameter Real T_ambient = 293.15 "Ambient K";
  Real T(start=333.15, fixed=true) "Body K";
initial equation
  T = T_ambient;
equation
  C * der(T) = G * (T_ambient - T);
end Cooling;
