function [Gasprofil_synth_Werte,Gasprofil_synth_Kennzahlen,Gasprofil_synth_Fit,SV_Tabelle_synth] = Berechnung_Waermeparameter(Time,Waerme,Temperatur,Fehldaten,Tagtyp_1_7,Gasprofile)
%% Vorbereiten der Daten

Tagtyp = char(Tagtyp_1_7);
Tagtyp = str2num(Tagtyp(:,1));

Waerme_std = timetable(Time,Waerme,Temperatur,Tagtyp,Fehldaten);

Waerme_Tagesmittel = retime(Waerme_std,"daily","mean");
Waerme_Tagessumme = retime(Waerme_std,"daily","sum");
Waerme_Tagessumme.Waerme(Waerme_Tagessumme.Waerme==0,:) = NaN;
Waerme_Tagesmittel.Waerme(Waerme_Tagesmittel.Waerme==0,:) = NaN;

% Berechnung der Allokationstemperatur
T_taeglich = Waerme_Tagesmittel.Temperatur;
T_D = zeros(numel(T_taeglich)+3,1);

T_D(1) = T_taeglich(1);
T_D(2) = T_taeglich(2);
T_D(3) = T_taeglich(3);

% Berechnung der Allokationstecmperatur
for i = 1:numel(T_taeglich)
	T_D(i+3) = T_taeglich(i);
end
T_Allokation = zeros(numel(T_taeglich),1);

for i = 1:numel(T_taeglich)
    if isnan(T_D(i+2)) & isnan(T_D(i+1)) & isnan(T_D(i)) 
        T_D(i+2) = T_D(i+3);
        T_D(i+1) = T_D(i+3);
        T_D(i) = T_D(i+3);
    end
	T_Allokation(i) = (T_D(i+3) + 0.5 * T_D(i+2) + 0.25 * T_D(i+1) + 0.125 * T_D(i))/(1 + 0.5 + 0.25 + 0.125);
end

% neuer timetable mit Allokationstemperatur
varNames = ["Q_Allokation","T_Allokation","Tagtyp","Fehldaten"];
Waerme_taeglich = timetable(Waerme_Tagessumme.Time,Waerme_Tagessumme.Waerme,T_Allokation,Waerme_Tagesmittel.Tagtyp,Waerme_Tagesmittel.Fehldaten,'VariableNames',varNames);

% Entfernen fehlerhafter Daten
Waerme_taeglich.Fehldaten(Waerme_taeglich.Fehldaten>0,:)=true;
Waerme_taeglich(Waerme_taeglich.Fehldaten==1,:)=[];
Waerme_Tagessumme.Fehldaten(Waerme_Tagessumme.Fehldaten>0,:)=true;
Waerme_Tagesmittel.Fehldaten(Waerme_Tagesmittel.Fehldaten>0,:)=true;

Tagtyp_taeglich = Waerme_taeglich.Tagtyp;
Q_Allokation = Waerme_taeglich.Q_Allokation;

%% Wochentagsfaktoren bestimmen
Wochentage_Matrix = zeros(7,2);
% erste Spalte: Anzahl der Tagtypen
% zweite Spalte: Summe der Q_Allokation Werte für jeweiligen Tagtyp

for i = 1:numel(Tagtyp_taeglich)
    switch Tagtyp_taeglich(i)
        case 1
            Wochentage_Matrix(1,1) = Wochentage_Matrix(1,1) + 1;
            Wochentage_Matrix(1,2) = Wochentage_Matrix(1,2) + Q_Allokation(i);
        case 2
            Wochentage_Matrix(2,1) = Wochentage_Matrix(2,1) + 1;
            Wochentage_Matrix(2,2) = Wochentage_Matrix(2,2) + Q_Allokation(i);
        case 3
            Wochentage_Matrix(3,1) = Wochentage_Matrix(3,1) + 1;
            Wochentage_Matrix(3,2) = Wochentage_Matrix(3,2) + Q_Allokation(i);
        case 4
            Wochentage_Matrix(4,1) = Wochentage_Matrix(4,1) + 1;
            Wochentage_Matrix(4,2) = Wochentage_Matrix(4,2) + Q_Allokation(i);
        case 5
            Wochentage_Matrix(5,1) = Wochentage_Matrix(5,1) + 1;
            Wochentage_Matrix(5,2) = Wochentage_Matrix(5,2) + Q_Allokation(i);
        case 6
            Wochentage_Matrix(6,1) = Wochentage_Matrix(6,1) + 1;
            Wochentage_Matrix(6,2) = Wochentage_Matrix(6,2) + Q_Allokation(i);
        case 7
            Wochentage_Matrix(7,1) = Wochentage_Matrix(7,1) + 1;
            Wochentage_Matrix(7,2) = Wochentage_Matrix(7,2) + Q_Allokation(i);
    end
end

Wochentagsfaktoren = Wochentage_Matrix(:,2)/Wochentage_Matrix(:,1);

% Normierung, sodass Summe der Faktoren 7 ergibt
Wochentagsfaktoren = (Wochentagsfaktoren/sum(Wochentagsfaktoren))*7;
Wochentagsfaktoren = transpose(Wochentagsfaktoren);

% Wochentagfaktoren den Tagtypen zuordnen:
F_WT = zeros(size(Tagtyp_taeglich,1),1);

F_WT(Tagtyp_taeglich==1) = Wochentagsfaktoren(1);
F_WT(Tagtyp_taeglich==2) = Wochentagsfaktoren(2);
F_WT(Tagtyp_taeglich==3) = Wochentagsfaktoren(3);
F_WT(Tagtyp_taeglich==4) = Wochentagsfaktoren(4);
F_WT(Tagtyp_taeglich==5) = Wochentagsfaktoren(5);
F_WT(Tagtyp_taeglich==6) = Wochentagsfaktoren(6);
F_WT(Tagtyp_taeglich==7) = Wochentagsfaktoren(7);

if F_WT(Tagtyp_taeglich==0)
    error("Fehler bei Tagtypen!");
end

%% Stundenfaktoren bestimmen
varNames = "T_Allokation";
Waerme_Allok = timetable(Waerme_Tagessumme.Time,T_Allokation,'VariableNames',varNames);
end_Allok = numel(Waerme_Allok);
Waerme_Allok.T_Allokation(end_Allok+1) = Waerme_Allok.T_Allokation(end_Allok);
Waerme_Allok.Properties.RowTimes(end_Allok+1) = Waerme_Allok.Time(end_Allok)+1;
Waerme_Allok.Jahresluecken = isnan(Waerme_Allok.T_Allokation);
Waerme_Allok_std = retime(Waerme_Allok,'hourly','previous');
Waerme_Allok_std(Waerme_Allok_std.Jahresluecken==1,:) = [];
Waerme_Allok_std(end,:) = [];
Waerme_Allok_std.Waerme = Waerme;
Waerme_Allok_std.Tagtyp_1_7 = Tagtyp_1_7;
Waerme_Allok_std.Fehldaten = Fehldaten;

Waerme_Allok_std = timetable2table(Waerme_Allok_std);
Waerme_Allok_std(Waerme_Allok_std.Fehldaten==1,:)=[];

Waerme_Intervalle = struct;
for i = 1:10
    Waerme_Intervalle(i).Waerme = Waerme_Allok_std;
end

Waerme_Intervalle(1).Waerme(Waerme_Allok_std.T_Allokation>=-15,:)=[];
Waerme_Intervalle(2).Waerme((Waerme_Allok_std.T_Allokation>=-10) | (Waerme_Allok_std.T_Allokation<-15),:)=[];
Waerme_Intervalle(3).Waerme((Waerme_Allok_std.T_Allokation>=-5) | (Waerme_Allok_std.T_Allokation<-10),:)=[];
Waerme_Intervalle(4).Waerme((Waerme_Allok_std.T_Allokation>=0) | (Waerme_Allok_std.T_Allokation<-5),:)=[];
Waerme_Intervalle(5).Waerme((Waerme_Allok_std.T_Allokation<0) | (Waerme_Allok_std.T_Allokation>=5),:)=[];
Waerme_Intervalle(6).Waerme((Waerme_Allok_std.T_Allokation<5) | (Waerme_Allok_std.T_Allokation>=10),:)=[];
Waerme_Intervalle(7).Waerme((Waerme_Allok_std.T_Allokation<10) | (Waerme_Allok_std.T_Allokation>=15),:)=[];
Waerme_Intervalle(8).Waerme((Waerme_Allok_std.T_Allokation<15) | (Waerme_Allok_std.T_Allokation>=20),:)=[];
Waerme_Intervalle(9).Waerme((Waerme_Allok_std.T_Allokation<20) | (Waerme_Allok_std.T_Allokation>=25),:)=[];
Waerme_Intervalle(10).Waerme(Waerme_Allok_std.T_Allokation<25,:)=[];

no_value = false(1,10);
Coefficients = zeros(numel(unique(Tagtyp_1_7)),10);
for i = 1:10
    Num_Tagtyp = numel(unique(Waerme_Intervalle(i).Waerme.Tagtyp_1_7));
    if Num_Tagtyp >= numel(unique(Tagtyp_1_7)) % prüfen, ob alle Tagtypen im Temperaturintervall enthalten
        SV = fitlm(Waerme_Intervalle(i).Waerme,'Waerme~Tagtyp_1_7');
        Coefficients(:,i) = SV.Coefficients.Estimate;
        for j = 2:numel(unique(Tagtyp_1_7))
            Coefficients(j,i) = Coefficients(j,i) + Coefficients(1,i);
        end
        
    elseif Num_Tagtyp < numel(unique(Tagtyp_1_7))
        no_value(i) = 1;
    end
end

% bei fehlenden Daten für niedrige Temperaturen
for i = 1:5
    if no_value(i) == 0
        k = i;
        for j = k:-1:2
            Coefficients(:,j-1) = Coefficients(:,k);
        end
        break
    else
    end
end
% bei fehlenden Daten für hohe Temperaturen
for i = 10:-1:5
    if no_value(i) == 0
        k = i;
        for j = k:9
            Coefficients(:,j+1) = Coefficients(:,k);
        end
        break
    else
    end
end
Mo=transpose(Coefficients(1:24,:));
Mo_sum = sum(Mo,2);
Mo = (Mo./Mo_sum)*100;

Di=transpose(Coefficients(25:48,:));
Di_sum = sum(Di,2);
Di = (Di./Di_sum)*100;

Mi=transpose(Coefficients(49:72,:));
Mi_sum = sum(Mi,2);
Mi = (Mi./Mi_sum)*100;

Do=transpose(Coefficients(73:96,:));
Do_sum = sum(Do,2);
Do = (Do./Do_sum)*100;

Fr=transpose(Coefficients(97:120,:));
Fr_sum = sum(Fr,2);
Fr = (Fr./Fr_sum)*100;

Sa=transpose(Coefficients(121:144,:));
Sa_sum = sum(Sa,2);
Sa = (Sa./Sa_sum)*100;

So=transpose(Coefficients(145:168,:));
So_sum = sum(So,2);
So = (So./So_sum)*100;

%% Schätzung der Profilkoeffizienten

T_Allokation = Waerme_taeglich.T_Allokation;
Q_Allokation = Waerme_taeglich.Q_Allokation;

% Berechnung des Kundenwerts
% mittels Linearisierung um 7°C < theta < 9°C
Waerme_taeglich_KW = Waerme_taeglich;
Waerme_taeglich_KW.F_WT = F_WT;
Waerme_taeglich_KW((Waerme_taeglich_KW.T_Allokation > 9)|(Waerme_taeglich_KW.T_Allokation < 7),:) = [];
Waerme_taeglich_KW.Q_Allokation = Waerme_taeglich_KW.Q_Allokation./Waerme_taeglich_KW.F_WT;


if numel(Waerme_taeglich_KW.T_Allokation) == 1 
    KW = Waerme_taeglich_KW.T_Allokation;
elseif numel(Waerme_taeglich_KW.T_Allokation) >= 2    
    % Linearisierung mit Formel: y=ax+b
    tbl = timetable2table(Waerme_taeglich_KW);
    mdl = fitlm(tbl,'Q_Allokation~T_Allokation');
    coeff = table2array(mdl.Coefficients);
    a = coeff(2,1);
    b = coeff(1,1);

    % Kundenwert mittels theta_0 = 8°C bestimmen:
    KW = a * 8 + b;
else
    error("Berechnung von KW nicht möglich, da kein Wert für T_Allokation im Bereich von 7°C bis 9°C!");
end

% Berechnung von h_theta aus Kundenwert und Wochentagsverteilung
h_theta = Q_Allokation./(KW*F_WT);

clear a b coeff

% Fitten der h(theta) Kurve mit Hilfe der Signoid+Linear Funktion
xy = cat(2,T_Allokation,h_theta);
xy(isnan(T_Allokation),:)=[];
xy = sortrows(xy,1);
x = xy(:,1);
y = xy(:,2);


Gaswerte=zeros(16,numel(Gasprofile));
for i = 1:numel(Gasprofile)
    Gaswerte(:,i) = Gasprofile(i).Werte;
end
Gaswerte = transpose(Gaswerte);
theta_0 = Gaswerte(1,5);
%Gaswerte(:,4)=[]; % D als Paramenter entfernen, um 8°C Wert zu fixieren
Gaswerte(:,5)=[]; % theta_0 entfernen, da konstant
Gaswerte(:,9:end)=[]; % Wochentagsfaktoren entfernen

% Definition der Startwerte und Iterationsgrenzen
Startwerte = mean(Gaswerte);
upper = max(Gaswerte);
lower = min(Gaswerte);

% Wert für 8 °C festlegen
x0 = 8;
y0 = 1;

% fit-funktion and fitkurve
ft = @(a,b,c,d,e,f,g,h,x) (a./((1+(b./(x-40))).^c)+d+max((e*x+f),(g*x+h)) + (y0 - a./((1+(b./(x0-40))).^c)-d-(max((e*x0+f),(g*x0+h)))));
[fitted_curve,gof] = fit(x,y,ft,'Lower',lower,'Upper',upper,'StartPoint',Startwerte,'Robust','Bisquare','Algorithm','Trust-Region');
coeff = coeffvalues(fitted_curve);

%% Ausgabe der Gasprofilkoeffizienten, Wochentags- und Stundenverteilungen

Gasprofil_synth_Werte = cat(2,coeff(1:4),theta_0,coeff(5:end),Wochentagsfaktoren);
Gasprofil_synth_Fit = fitted_curve;
Gasprofil_synth_Kennzahlen = gof;

SV_Tabelle_synth = struct;

SV_Tabelle_synth.Montag = Mo;
SV_Tabelle_synth.Dienstag = Di;
SV_Tabelle_synth.Mittwoch = Mi;
SV_Tabelle_synth.Donnerstag = Do;
SV_Tabelle_synth.Freitag = Fr;
SV_Tabelle_synth.Samstag = Sa;
SV_Tabelle_synth.Sonntag = So;