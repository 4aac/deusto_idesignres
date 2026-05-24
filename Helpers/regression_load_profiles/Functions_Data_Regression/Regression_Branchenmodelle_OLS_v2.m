function [Branchenmodell_ges,Referenzzeitreihen] = Regression_Branchenmodelle_OLS_v2(Einzelmodelle,Predictors,Variante,Variante_Betriebsruhe)
    % Betriebsruhe anordnen
    B = zeros(numel(Predictors.Betriebsruhe),1);
    for j = 1:numel(Predictors.Betriebsruhe)
        if Predictors.Betriebsruhe(j) == "false"
            B(j) = 0;
        else
            B(j) = 1;
        end
    end
    B = logical(B);
    B_inv = ~B;
    B_num = double(B);
    B_inv_num = double(B_inv);
    
    % Umwandeln der Prädiktoren in table:
    Predictors_tbl = timetable2table(Predictors);

    % Generierung der Referenzzeitreihen aus den Einzelmodellen:
    Referenzzeitreihen = struct;
    for i = 1:numel(Einzelmodelle)
        Referenzzeitreihen(i).Standort = Einzelmodelle(i).Standort;
        Referenzzeitreihen(i).Zeitreihe_normiert = Predictors;
        Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang_Normalbetrieb = predict(Einzelmodelle(i).Normalbetrieb,Predictors_tbl);
        Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang_Betriebsruhe = predict(Einzelmodelle(i).Betriebsruhe,Predictors_tbl);
        Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang = Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang_Normalbetrieb.*B_inv_num + Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang_Betriebsruhe.*B_num;
        if i == 1
            B_Branche = B;
        else
            B_Branche = cat(1,B_Branche,B);
        end
    end
    B_Branche_inv = ~B_Branche;

    % Zusammenführen der Referenzzeitreihen zu einer großen Zeitreihe
    for j = 1:numel(Einzelmodelle)
        if j == 1
            Referenzzeitreihen_ges  = Referenzzeitreihen(j).Zeitreihe_normiert;
        else
            Referenzzeitreihen_ges = [Referenzzeitreihen_ges;Referenzzeitreihen(j).Zeitreihe_normiert];
        end
    end

    % Generierung des Branchenmodells für Normalbetrieb und Betriebsruhe
    Referenzzeitreihen_ges = timetable2table(Referenzzeitreihen_ges);
    Normalbetrieb = fitlm(Referenzzeitreihen_ges,Variante);
    Branchenmodell_Normalbetrieb = compact(Normalbetrieb);
    Betriebsruhe = fitlm(Referenzzeitreihen_ges,Variante_Betriebsruhe,'Exclude',B_Branche_inv);
    Branchenmodell_Betriebsruhe = compact(Betriebsruhe);
    
    % Generierung des Structs für das Branchenmodell
    Branchenmodell_ges = struct;
    Branchenmodell_ges.Normalbetrieb = Branchenmodell_Normalbetrieb;
    Branchenmodell_ges.Betriebsruhe = Branchenmodell_Betriebsruhe;

    % Generierung der Referenzzeitreihe aus dem Branchenmodell:
    Branchenmodell_ges.Referenzzeitreihen = Predictors;
    Branchenmodell_ges.Referenzzeitreihen.Lastgang_Normalbetrieb = predict(Branchenmodell_Normalbetrieb,Predictors_tbl);
    Branchenmodell_ges.Referenzzeitreihen.Lastgang_Betriebsruhe = predict(Branchenmodell_Betriebsruhe,Predictors_tbl);
    Branchenmodell_ges.Referenzzeitreihen.Lastgang = Branchenmodell_ges.Referenzzeitreihen.Lastgang_Normalbetrieb.*B_inv + Branchenmodell_ges.Referenzzeitreihen.Lastgang_Betriebsruhe.*B_num;

    V_vek = zeros(numel(Einzelmodelle),4);
    for i = 1:numel(Einzelmodelle)
        V_vek(i,1) = Einzelmodelle(i).V_M_Buero_Produktion;
        V_vek(i,2) = Einzelmodelle(i).V_JV_M_Buero;
        V_vek(i,3) = Einzelmodelle(i).V_JV_M_Produktion;
        V_vek(i,4) = Einzelmodelle(i).V_JV_F_Produktion;
    end
%     V_vek_mean = mean(V_vek);
%     Branchenmodell_ges.V_vek = V_vek;
%     Branchenmodell_ges.V_M_Buero_Produktion = V_vek_mean(1);
%     Branchenmodell_ges.V_JV_M_Buero = V_vek_mean(2);
%     Branchenmodell_ges.V_JV_M_Produktion = V_vek_mean(3);
%     Branchenmodell_ges.V_JV_F_Produktion = V_vek_mean(4);

    % Mittelwert
    V_vek_mean = mean(V_vek);

    % Ausgabe Mittelwerte
    Branchenmodell_ges.V_M_Buero_Produktion(1) = V_vek_mean(1);
    Branchenmodell_ges.V_JV_M_Buero(1) = V_vek_mean(2);
    Branchenmodell_ges.V_JV_M_Produktion(1) = V_vek_mean(3);
    Branchenmodell_ges.V_JV_F_Produktion(1) = V_vek_mean(4);

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
    Branchenmodell_ges.V_M_Buero_Produktion(2) = V_vek_005(1);
    Branchenmodell_ges.V_JV_M_Buero(2) = V_vek_005(2);
    Branchenmodell_ges.V_JV_M_Produktion(2) = V_vek_005(3);
    Branchenmodell_ges.V_JV_F_Produktion(2) = V_vek_005(4);

    Branchenmodell_ges.V_M_Buero_Produktion(3) = V_vek_095(1);
    Branchenmodell_ges.V_JV_M_Buero(3) = V_vek_095(2);
    Branchenmodell_ges.V_JV_M_Produktion(3) = V_vek_095(3);
    Branchenmodell_ges.V_JV_F_Produktion(3) = V_vek_095(4);
end