function [Temperaturzeitreihe,Globale_Strahlungzeitreihe] = Pruefung_Schaltjahr(Temperatur,Globale_Strahlung,Time)
    Temperaturzeitreihe = Temperatur;
    Globale_Strahlungzeitreihe = Globale_Strahlung;
    num_Temp = numel(Temperatur);
    num_GS = numel(Globale_Strahlung);
    num_Time = numel(Time);

    if num_Temp == num_GS
        if num_Time > num_Temp
            k = num_Time - num_Temp;
            j = 0;
            for i = (num_Temp-k):num_Temp
                Temperaturzeitreihe(num_Temp+j) = Temperaturzeitreihe(i);
                Globale_Strahlungzeitreihe(num_Temp+j) = Globale_Strahlungzeitreihe(i);
                j = j + 1;
            end
        elseif num_Time < num_Temp
            Temperaturzeitreihe((num_Time+1):end) = [];
            Globale_Strahlungzeitreihe((num_Time+1):end) = [];
        end
    else
        warning("Dimension von Temperatur und globaler Strahlung passt nicht!");
    end
end