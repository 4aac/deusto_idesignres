function [Branchenmodell_ges,Referenzzeitreihen] = Regression_Branchenmodelle_OLS(Einzelmodelle,Predictors,Variante)
    % Umwandeln der Prädiktoren in table:
    Predictors_tbl = timetable2table(Predictors);

    Referenzzeitreihen = struct;
    for i = 1:numel(Einzelmodelle)
        Referenzzeitreihen(i).Standort = Einzelmodelle(i).Standort;
        Referenzzeitreihen(i).Zeitreihe_normiert = Predictors;
        Referenzzeitreihen(i).Zeitreihe_normiert.Lastgang = predict(Einzelmodelle(i).Normalbetrieb,Predictors_tbl);
    end
    for j = 1:numel(Einzelmodelle)
        if j == 1
            Referenzzeitreihen_ges  = Referenzzeitreihen(j).Zeitreihe_normiert;
        else
            Referenzzeitreihen_ges = [Referenzzeitreihen_ges;Referenzzeitreihen(j).Zeitreihe_normiert];
        end
    end
    Referenzzeitreihen_ges = timetable2table(Referenzzeitreihen_ges);
    Normalbetrieb = fitlm(Referenzzeitreihen_ges,Variante);
    Branchenmodell_Normalbetrieb = compact(Normalbetrieb);



    Branchenmodell_ges = struct;
    Branchenmodell_ges.Normalbetrieb = Branchenmodell_Normalbetrieb;
    Branchenmodell_ges.Referenzzeitreihen = Predictors;
    Branchenmodell_ges.Referenzzeitreihen.Lastgang = predict(Branchenmodell_Normalbetrieb,Predictors_tbl);
    
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