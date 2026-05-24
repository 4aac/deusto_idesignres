function [Branchenmodell,Branchenmodell_anonymisiert,Referenzzeitreihen] = Synthese_Branchenmodell(Einzelmodelle,Feiertage_2000_bis_2050,Klimadaten_DE,Predictors_1Jahr)
load('Gasprofile_Daten.mat');
Branchenmodell = struct;

Vektor = ones(8760,1);
varNames = ["Tagtyp_1_7","Temperatur"];
j = 2012;
for i = 15:24
    % Tagtypen- und Zeitindexvektor für Standort zuordnen:
    Zeitformat = Zeitzuordnung(j,"DE",Vektor,Feiertage_2000_bis_2050);
    
    Time = Zeitformat.Time;
    Tagtyp_1_7 = Zeitformat.Tagtyp_1_7_categorical;
    Temperatur = Klimadaten_DE(i).Zeitreihen_stuendlich.Temperatur;

    if i == 15
        Predictors = timetable(Time,Tagtyp_1_7,Temperatur,'VariableNames',varNames);
    elseif i > 15
        P = timetable(Time,Tagtyp_1_7,Temperatur);
        Predictors = [Predictors;P];
    end
    j = j+1;
end
Time_offset = 0;
for i = 1:numel(Einzelmodelle)
    Waermebedarf = 1000;
    Waermebedarf_ges = 10 * Waermebedarf;
    Waermeprofil = Berechnung_Waermezeitreihe_synthetisch(Predictors.Time,Waermebedarf_ges,Predictors.Temperatur,Predictors.Tagtyp_1_7,i,Einzelmodelle,Einzelmodelle);
    Waermeprofil.Tagtyp_1_7 = Predictors.Tagtyp_1_7;

    if i == 1
        Waermeprofil_Referenz = Waermeprofil;
    elseif i > 1
        Waermeprofil_Referenz.Time = Waermeprofil_Referenz.Time + Time_offset;
        Waermeprofil_Referenz = [Waermeprofil_Referenz;Waermeprofil];
    end
    Time_offset = (numel(Waermeprofil_Referenz.Time)/24) + Time_offset;
    Referenzzeitreihe = Berechnung_Waermezeitreihe_synthetisch(Predictors_1Jahr.Time,Waermebedarf,Predictors_1Jahr.Temperatur,Predictors_1Jahr.Tagtyp_1_7,i,Einzelmodelle,Einzelmodelle);
    Referenzzeitreihe_norm = Referenzzeitreihe;
    Referenzzeitreihe_norm.Waerme = Referenzzeitreihe.Waerme/sum(Referenzzeitreihe.Waerme);
    Referenzzeitreihe_norm.Fehldaten = false(numel(Referenzzeitreihe_norm.Waerme),1);
    Referenzzeitreihe_norm.Tagtyp_1_7 = Predictors_1Jahr.Tagtyp_1_7;
    Referenzzeitreihe_norm.Properties.VariableNames(1) = "Lastgang";
    Referenzzeitreihen(i).Standort = Einzelmodelle(i).Standort;
    Referenzzeitreihen(i).Zeitreihe_normiert = Referenzzeitreihe_norm;
end

Time = Waermeprofil_Referenz.Time;
Waerme = Waermeprofil_Referenz.Waerme;
Temperatur = Waermeprofil_Referenz.Temperatur;
Tagtyp_1_7 = Waermeprofil_Referenz.Tagtyp_1_7;
Fehldaten = false(numel(Waerme),1);

[Gasprofil_synth_Werte,Gasprofil_synth_Kennzahlen,Gasprofil_synth_Fit,SV_Tabelle_synth] = Berechnung_Waermeparameter(Time,Waerme,Temperatur,Fehldaten,Tagtyp_1_7,Gasprofile);

Branchenmodell.Werte = Gasprofil_synth_Werte;
Branchenmodell.Montag = SV_Tabelle_synth.Montag;
Branchenmodell.Dienstag = SV_Tabelle_synth.Dienstag;
Branchenmodell.Mittwoch = SV_Tabelle_synth.Mittwoch;
Branchenmodell.Donnerstag = SV_Tabelle_synth.Donnerstag;
Branchenmodell.Freitag = SV_Tabelle_synth.Freitag;
Branchenmodell.Samstag = SV_Tabelle_synth.Samstag;
Branchenmodell.Sonntag = SV_Tabelle_synth.Sonntag;
Branchenmodell.Gasprofil_Kennzahlen = Gasprofil_synth_Kennzahlen;
Branchenmodell.Gasprofil_synth_Fit = Gasprofil_synth_Fit;

Branche_Referenz = Berechnung_Waermezeitreihe_synthetisch(Predictors_1Jahr.Time,Waermebedarf,Predictors_1Jahr.Temperatur,Predictors_1Jahr.Tagtyp_1_7,1,Branchenmodell,Branchenmodell);
Branchenmodell.Referenzzeitreihen = Branche_Referenz;
Branchenmodell.Referenzzeitreihen.Waerme = Branche_Referenz.Waerme/sum(Branche_Referenz.Waerme);
Branchenmodell.Referenzzeitreihen.Properties.VariableNames(1) = "Lastgang";

V_vek = zeros(numel(Einzelmodelle),4);
for i = 1:numel(Einzelmodelle)
    V_vek(i,1) = Einzelmodelle(i).V_M_Buero_Produktion;
    V_vek(i,2) = Einzelmodelle(i).V_JV_M_Buero;
    V_vek(i,3) = Einzelmodelle(i).V_JV_M_Produktion;
    V_vek(i,4) = Einzelmodelle(i).V_JV_F_Produktion;
end
% Mittelwert
V_vek_mean = mean(V_vek);

% Ausgabe Mittelwerte
Branchenmodell.V_M_Buero_Produktion(1) = V_vek_mean(1);
Branchenmodell.V_JV_M_Buero(1) = V_vek_mean(2);
Branchenmodell.V_JV_M_Produktion(1) = V_vek_mean(3);
Branchenmodell.V_JV_F_Produktion(1) = V_vek_mean(4);

% 95 % Konfidenzintervall berechnen
V_vek_std = std(V_vek);
n = numel(V_vek(1,:));

% Berechnung über t-Werte, da Stichprobe sehr klein
alphaup = 1-0.05/2;
alphalow = 0.05/2;
upp = tinv(alphaup,n-1);
low = tinv(alphalow,n-1);

V_vek_005 = V_vek_mean + low * (V_vek_std)/(n);
V_vek_095 = V_vek_mean + upp * (V_vek_std)/(n);

% Ausgabe Konfidenzintervalle
Branchenmodell.V_M_Buero_Produktion(2) = V_vek_005(1);
Branchenmodell.V_JV_M_Buero(2) = V_vek_005(2);
Branchenmodell.V_JV_M_Produktion(2) = V_vek_005(3);
Branchenmodell.V_JV_F_Produktion(2) = V_vek_005(4);

Branchenmodell.V_M_Buero_Produktion(3) = V_vek_095(1);
Branchenmodell.V_JV_M_Buero(3) = V_vek_095(2);
Branchenmodell.V_JV_M_Produktion(3) = V_vek_095(3);
Branchenmodell.V_JV_F_Produktion(3) = V_vek_095(4);

% Hier werden nur die wirklich notwendigen Daten gespeichert
Branchenmodell_anonymisiert.Werte = Branchenmodell.Werte;
Branchenmodell_anonymisiert.Montag = Branchenmodell.Montag;
Branchenmodell_anonymisiert.Dienstag = Branchenmodell.Dienstag;
Branchenmodell_anonymisiert.Mittwoch = Branchenmodell.Mittwoch;
Branchenmodell_anonymisiert.Donnerstag = Branchenmodell.Donnerstag;
Branchenmodell_anonymisiert.Freitag	= Branchenmodell.Freitag;
Branchenmodell_anonymisiert.Samstag	= Branchenmodell.Samstag;
Branchenmodell_anonymisiert.Sonntag	= Branchenmodell.Sonntag;
Branchenmodell_anonymisiert.V_M_Buero_Produktion = Branchenmodell.V_M_Buero_Produktion;
Branchenmodell_anonymisiert.V_JV_M_Buero = Branchenmodell.V_JV_M_Buero;
Branchenmodell_anonymisiert.V_JV_M_Produktion = Branchenmodell.V_JV_M_Produktion;
Branchenmodell_anonymisiert.V_JV_F_Produktion = Branchenmodell.V_JV_F_Produktion;


end