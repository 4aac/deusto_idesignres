function [Buerozeitreihe] = Berechnung_Buerozeitreihe_Strom(Stromverbrauch_Buero,Time,Tagtyp_Index,Temperatur,Globale_Strahlung,Buero_Modell,Betriebsruhe)
    
    % Werktage auf Samstage ändern, wenn Betriebsruhe
    % categorical in char umwandeln
    Tagtyp_temp = char(Tagtyp_Index);
    Tagtyp_temp_a = Tagtyp_temp(:,1);
    Tagtyp_temp_b = Tagtyp_temp(:,[2,3,4,5,6,7]);

    for i = 1:numel(Tagtyp_Index)
        if Tagtyp_temp_a(i) == '1' || Tagtyp_temp_a(i) == '2' || Tagtyp_temp_a(i) == '3' || Tagtyp_temp_a(i) == '4' || Tagtyp_temp_a(i) == '5'
            if Betriebsruhe(i) == "true"
                Tagtyp_temp_a(i) = '6';
            end
        elseif Tagtyp_temp_a(i) == '6' || Tagtyp_temp_a(i) == '7'
        
        end
    end
    Tagtyp_Index = categorical(string([Tagtyp_temp_a Tagtyp_temp_b]));

    varNames = ["Temperatur","Globale_Strahlung","Tagtyp_Index"];
    Zeitreihe = timetable(Time,Temperatur,Globale_Strahlung,Tagtyp_Index,'VariableNames',varNames);
    
    X = timetable2table(Zeitreihe);

    Buerozeitreihe = predict(Buero_Modell,X);
    P_norm = sum(Buerozeitreihe)/4;

    Buerozeitreihe = Buerozeitreihe * Stromverbrauch_Buero / P_norm;
end