function [Zeitreihen_regr] = Zusammenfuehrung_Zeitreihen(Zeitreihen)

% Standortnummerierung und in array übernehmen
Standortvek = zeros(numel(Zeitreihen),1);
for i = 1:numel(Zeitreihen)
    Standortvek(i,1) = Zeitreihen(i).Standort;
end
% struct für die spätere Regression definieren
Zeitreihen_regr = struct;
Standortvek_unique = unique(Standortvek);

for i = 1:numel(Standortvek_unique)
    Zeitreihen_regr(i).Standort = Standortvek_unique(i,1);
end

% Zusammenführen der Zeitreihen mehrerer Kalenderjahre je Standort
for i = 1:numel(Standortvek_unique)
    Standort = Standortvek_unique(i);
    pos_Standortvek = find(Standortvek == Standort);

    V_M_Buero_Produktion = Zeitreihen(pos_Standortvek(1)).V_M_Buero_Produktion;
    V_JV_M_Buero = Zeitreihen(pos_Standortvek(1)).V_JV_M_Buero;
    V_JV_M_Produktion = Zeitreihen(pos_Standortvek(1)).V_JV_M_Produktion;
    V_JV_F_Produktion = Zeitreihen(pos_Standortvek(1)).V_JV_F_Produktion;

        Z = Zeitreihen(pos_Standortvek(1)).Zeitreihe_normiert;
        if numel(pos_Standortvek) > 1
            for j = 2:numel(pos_Standortvek)
                Z = [Z;Zeitreihen(pos_Standortvek(j)).Zeitreihe_normiert];
                V_M_Buero_Produktion = V_M_Buero_Produktion + Zeitreihen(pos_Standortvek(j)).V_M_Buero_Produktion;
                V_JV_M_Buero = V_JV_M_Buero + Zeitreihen(pos_Standortvek(j)).V_JV_M_Buero;
                V_JV_M_Produktion = V_JV_M_Produktion + Zeitreihen(pos_Standortvek(j)).V_JV_M_Produktion;
                V_JV_F_Produktion = V_JV_F_Produktion + Zeitreihen(pos_Standortvek(j)).V_JV_F_Produktion;
            end
            V_M_Buero_Produktion = V_M_Buero_Produktion / j;
            V_JV_M_Buero = V_JV_M_Buero / j;
            V_JV_M_Produktion = V_JV_M_Produktion / j;
            V_JV_F_Produktion = V_JV_F_Produktion / j;
        end
    Zeitreihen_regr(i).Standort = Standort;
    Zeitreihen_regr(i).Zeitreihe_normiert = Z;
    Zeitreihen_regr(i).V_M_Buero_Produktion = V_M_Buero_Produktion;
    Zeitreihen_regr(i).V_JV_M_Buero = V_JV_M_Buero;
    Zeitreihen_regr(i).V_JV_M_Produktion = V_JV_M_Produktion;
    Zeitreihen_regr(i).V_JV_F_Produktion = V_JV_F_Produktion;

end
end