function [Einzelmodelle] = Regression_Einzelmodelle_OLS_v2(Zeitreihen,Variante,Variante_Betriebsruhe)
Einzelmodelle = struct;

% Regression nach den vorgegeben Varianten
for i = 1:numel(Zeitreihen)
    Einzelmodelle(i).Standort = Zeitreihen(i).Standort;
    Zeitreihen(i).Zeitreihe_normiert.Lastgang = Zeitreihen(i).Zeitreihe_normiert.Lastgang;
    B = zeros(numel(Zeitreihen(i).Zeitreihe_normiert.Betriebsruhe),1);
    for j = 1:numel(Zeitreihen(i).Zeitreihe_normiert.Betriebsruhe)
        if Zeitreihen(i).Zeitreihe_normiert.Betriebsruhe(j) == "false"
            B(j) = 0;
        else
            B(j) = 1;
        end
    end
    B = logical(B);
    Zeitreihen(i).Zeitreihe_normiert.Betriebsruhe = B;

    % Zeitreihe in Tabelle umwandeln:
    tbl = timetable2table(Zeitreihen(i).Zeitreihe_normiert);
    tbl.Betriebsruhe_inv = ~tbl.Betriebsruhe;
    tbl(tbl.Fehldaten==1,:) = [];
    
    % Regression der Einzelmodelle:
    Normalbetrieb = fitlm(tbl,Variante);%,'Exclude',tbl.Betriebsruhe
    Einzelmodelle(i).Normalbetrieb = compact(Normalbetrieb);
    Betriebsruhe = fitlm(tbl,Variante_Betriebsruhe,'Exclude',tbl.Betriebsruhe_inv);
    Einzelmodelle(i).Betriebsruhe = compact(Betriebsruhe);
    
    Einzelmodelle(i).V_M_Buero_Produktion = Zeitreihen(i).V_M_Buero_Produktion;
    Einzelmodelle(i).V_JV_M_Buero = Zeitreihen(i).V_JV_M_Buero;
    Einzelmodelle(i).V_JV_M_Produktion = Zeitreihen(i).V_JV_M_Produktion;
    Einzelmodelle(i).V_JV_F_Produktion = Zeitreihen(i).V_JV_F_Produktion;
end