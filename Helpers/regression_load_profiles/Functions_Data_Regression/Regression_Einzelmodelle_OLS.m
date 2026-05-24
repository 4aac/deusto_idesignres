function [Einzelmodelle] = Regression_Einzelmodelle_OLS(Zeitreihen,Variante)
Einzelmodelle = struct;

% Regression nach den vorgegeben Varianten
for i = 1:numel(Zeitreihen)
    Einzelmodelle(i).Standort = Zeitreihen(i).Standort;

    % Zeitreihe in Tabelle umwandeln:
    tbl = timetable2table(Zeitreihen(i).Zeitreihe_normiert);
    tbl(tbl.Fehldaten==1,:) = [];
    
    % Regression der Einzelmodelle:
    Normalbetrieb = fitlm(tbl,Variante);
    Einzelmodelle(i).Normalbetrieb = compact(Normalbetrieb);
    
    Einzelmodelle(i).V_M_Buero_Produktion = Zeitreihen(i).V_M_Buero_Produktion;
    Einzelmodelle(i).V_JV_M_Buero = Zeitreihen(i).V_JV_M_Buero;
    Einzelmodelle(i).V_JV_M_Produktion = Zeitreihen(i).V_JV_M_Produktion;
    Einzelmodelle(i).V_JV_F_Produktion = Zeitreihen(i).V_JV_F_Produktion;
end