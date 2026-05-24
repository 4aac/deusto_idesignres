function [Einzelmodelle] = Synthese_Einzelmodelle(Zeitreihen_Regression)
load('Gasprofile_Daten.mat');
Einzelmodelle = struct;

for i = 1:numel(Zeitreihen_Regression)
    Time = Zeitreihen_Regression(i).Zeitreihe_normiert.Time;
    Waerme = Zeitreihen_Regression(i).Zeitreihe_normiert.Lastgang*1000;
    Temperatur = Zeitreihen_Regression(i).Zeitreihe_normiert.Temperatur;
    Fehldaten = Zeitreihen_Regression(i).Zeitreihe_normiert.Fehldaten;
    Tagtyp_1_7 = Zeitreihen_Regression(i).Zeitreihe_normiert.Tagtyp_1_7;
    [Gasprofil_synth_Werte,Gasprofil_synth_Kennzahlen,Gasprofil_synth_Fit,SV_Tabelle_synth] = Berechnung_Waermeparameter(Time,Waerme,Temperatur,Fehldaten,Tagtyp_1_7,Gasprofile);
    
    Einzelmodelle(i).Standort = Zeitreihen_Regression(i).Standort;
    Einzelmodelle(i).Werte = Gasprofil_synth_Werte;
    Einzelmodelle(i).Montag = SV_Tabelle_synth.Montag;
    Einzelmodelle(i).Dienstag = SV_Tabelle_synth.Dienstag;
    Einzelmodelle(i).Mittwoch = SV_Tabelle_synth.Mittwoch;
    Einzelmodelle(i).Donnerstag = SV_Tabelle_synth.Donnerstag;
    Einzelmodelle(i).Freitag = SV_Tabelle_synth.Freitag;
    Einzelmodelle(i).Samstag = SV_Tabelle_synth.Samstag;
    Einzelmodelle(i).Sonntag = SV_Tabelle_synth.Sonntag;
    Einzelmodelle(i).Gasprofil_Kennzahlen = Gasprofil_synth_Kennzahlen;
    Einzelmodelle(i).Gasprofil_synth_Fit = Gasprofil_synth_Fit;
    Einzelmodelle(i).V_M_Buero_Produktion = Zeitreihen_Regression(i).V_M_Buero_Produktion;
    Einzelmodelle(i).V_JV_M_Buero = Zeitreihen_Regression(i).V_JV_M_Buero;
    Einzelmodelle(i).V_JV_M_Produktion = Zeitreihen_Regression(i).V_JV_M_Produktion;
    Einzelmodelle(i).V_JV_F_Produktion = Zeitreihen_Regression(i).V_JV_F_Produktion;
end


end