function DayAhead = DayAheadzuordnung(Jahr,struct_DayAhead,Zeitreihe)

Jahrvektor = zeros(numel(struct_DayAhead),1);
for i = 1:numel(struct_DayAhead)
    Jahrvektor(i) = struct_DayAhead(i).Jahr;
end
index = find(Jahrvektor==Jahr);
if (numel(Zeitreihe) == 35040 || numel(Zeitreihe) == 35136)
   % 15-minütige Auflösung (für Stromzeitreihen)
   DayAhead = struct_DayAhead(index).DayAhead.DayAhead;
else
   warning('Zeitreihenvektor hat falsche Dimension!');
end
end

