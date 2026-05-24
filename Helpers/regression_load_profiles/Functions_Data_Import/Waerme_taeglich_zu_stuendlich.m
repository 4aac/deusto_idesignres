%% Grobe Näherung einer stündlichen Wärmezeitreihe aus Tagessummen und Stromzeitreihe
% Eingaben:
Jahr = 2018;
zeitreihe = Waermezeitreihe_taeglich;
strom = Stromzeitreihe;


% Berechnung
if exist('Feiertage_2000_bis_2050','var') == 0
    load('Feiertage_2000_bis_2050.mat');
end
Zeitformat = Zeitzuordnung_v2(Jahr,"DE",strom,Feiertage_2000_bis_2050);
Time = Zeitformat.Time;


zeitreihe_std = retime(zeitreihe,'hourly','previous');
zeitreihe_std(end,:)=[];

Waermezeitreihe_std = zeitreihe_std.Lastgang;

Waerme = zeitreihe_std.Lastgang;

varNames = "Lastgang";
zeitreihe_strom = timetable(Time,strom,'VariableNames',varNames);
zeitreihe_strom(end+1,:)=zeitreihe_strom(end,:);

if (numel(Last) == 8760 || numel(Last) == 8784)
    zeitreihe_strom.Time(end)=zeitreihe_strom.Time(end-1)+1;
end

zeitreihe_strom = retime(zeitreihe_strom,"daily","sum");
zeitreihe_strom = retime(zeitreihe_strom,'hourly','previous');
zeitreihe_strom(end,:)=[];

Tagessumme_strom = zeitreihe_strom.Lastgang;
Tagessumme_waerme = Waerme;

Waermezeitreihe_stuendlich = (Tagessumme_waerme./Tagessumme_strom).*strom;