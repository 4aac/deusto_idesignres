function [Betriebsruhe] = ZuordnungBetriebsferien(Zeitreihe,Beginn,Ende,Jahr)
% Betriebsferien zuordnen
Jahrstr = num2str(Jahr);
Uhrzeit_Beginn = " 00:00:00";
Uhrzeit_Ende = " 00:15:00";

Beginn = append(Beginn,Jahrstr,Uhrzeit_Beginn);
Ende = append(Ende,Jahrstr,Uhrzeit_Ende);

Beginn = datetime(Beginn);
Ende = datetime(Ende);

% Matrix für die einzelnen Betriebsruhenzeiträume erstellen:
Betriebsruhematrix = zeros(numel(Zeitreihe),numel(Beginn));
for j = 1:numel(Beginn)
    Betriebsruhematrix(:,j) = isbetween(Zeitreihe,Beginn(j),(Ende(j)+1),'open');
end

% Zusammenführen der einzelnen Zeiträume mittels logischem OR für die
% einzelnen Matrixspalten
if numel(Beginn) > 1
    Betriebsruhe = Betriebsruhematrix(:,1) | Betriebsruhematrix(:,2);
else
    Betriebsruhe = Betriebsruhematrix;
end

for j = 1:(numel(Beginn)-1)
    k = j+1;
    Betriebsruhe = Betriebsruhe | Betriebsruhematrix(:,k);
end

Betriebsruhe = string(Betriebsruhe);
Betriebsruhe(Betriebsruhe=="0")="false";
Betriebsruhe(Betriebsruhe=="1")="true";
Betriebsruhe = categorical(Betriebsruhe);