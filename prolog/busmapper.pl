
:- [db].



car_estimated_arrive(Car, Sta, Time, arrive) :-
  data_car_stop(Car, Sta, Time, arrive), !.

car_estimated_arrive(Car, Sta, TimeArrive, leave) :-
  data_car_stop(Car, Sta, TimeLeaves, leave),
  timestr_to_seconds(TimeLeaves, TimeLeavesSecs),
  TimeEstArriveSecs = TimeLeavesSecs - 60,



car_arrives(Car, Sta, Time) :-
  data_car(Car),
  data_station(Sta),
  car_estimated_arrive(Car, Sta, Time, Type),



timestr_to_seconds(TimeStrAtom, AllSeconds) :-
  atom_string(TimeStrAtom, TimeStr),
  split_string(TimeStr, ":", "", L),
  [Hours, Minutes] = L,
  AllSeconds = ((Hours*60)+Minutes)*60.


seconds_to_timestr(AllSeconds, TimeStrAtom) :-
  TimeStrAtom
  atom_string(TimeStrAtom, TimeStr),
  split_string(TimeStr, ":", "", L),
  [Hours, Minutes] = L,
  AllSeconds = ((Hours*60)+Minutes)*60.



build_table_for_car(Car) :-
  writeln(['Car is', Car]),
  forall(car_arrives(Car, X, Y), writeln([X,Y])).


:- findall([Car,Sta,Time], car_arrives(Car,Sta,Time), Ls), writeln(Ls).
