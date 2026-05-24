function Zeitreihe_15min = Umrechnung_Zeitreihe15min(Zeitreihe_std,Methode)
    if (numel(Zeitreihe_std) == 8760 || numel(Zeitreihe_std) == 8784)
        switch Methode
            case "linear"
                y = Zeitreihe_std;
                Zeitreihe_15min = interp(y,4); % lineare Interpolation
            case "spline"
                y = Zeitreihe_std;
                i = size(y,1);
                j = i-1;
        
                index_std = 0:j;                 % Zeitindex stündlich
                index_15 = 0:.25:i;              % Zeitindex 15-minütig
                yy = spline(index_std,y,index_15);  % Spline Ansatz aus VDEW 1999

                yy(end)=[]; % löschen des letzten Wertes, da sonst einer zuviel

                % Ausgabe der umgerechneten Zeitreihe
                Zeitreihe_15min = transpose(yy);
        end
    elseif (numel(Zeitreihe_std) == 35040 || numel(Zeitreihe_std) == 35136)
        % 15-minütige Auflösung
        Zeitreihe_15min = Zeitreihe_std;
    else
        warning('Zeitreihenvektor hat falsche Dimension!');
    end
end

