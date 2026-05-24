function [Bewertung,Bewertung_Standorte,DayAhead_plausibel] = Regression_Einzelmodelle_Varianten_OLS(Zeitreihen,Varianten)

Kennzahlen = zeros(numel(Varianten),5,numel(Zeitreihen));
Varianten_DayAhead = contains(Varianten,"DayAhead");
DayAhead_plausibel = "Ja";

% Regression nach den vorgegeben Varianten
for i = 1:numel(Zeitreihen)
    % Zeitreihe in Tabelle umwandeln:
    tbl = timetable2table(Zeitreihen(i).Zeitreihe_normiert);
    tbl(tbl.Fehldaten==1,:) = [];
    for j = 1:numel(Varianten)
        % Regression der Einzelmodelle:
        
        LinearesModell = fitlm(tbl,Varianten(j));
        Kennzahlen(j,2,i) = LinearesModell.Rsquared.Ordinary;
        Kennzahlen(j,3,i) = LinearesModell.Rsquared.Adjusted;

        % MAPE berechnen
        measured = LinearesModell.Variables.Lastgang;
        predicted = LinearesModell.Fitted;
        m = abs((measured-predicted)./(measured));
        MAPE = (1/numel(measured))*sum(m);
        Kennzahlen(j,4,i) = MAPE;

        % nRMSE berechnen
        % squared error
        SE = (measured-predicted).^2;
        % root mean square error
        RMSE = sqrt((1/LinearesModell.NumObservations)*sum(SE));
        % normalized root mean square error
        nRMSE = RMSE / (max(measured)-min(measured));

        Kennzahlen(j,5,i) = nRMSE;
                
        % wenn der Regressionskoeffizient für DayAhead positiv ist, ist der
        % DayAhead Preis nicht aussagekräftig für das Lastverhalten
        if Varianten_DayAhead(j)
            if LinearesModell.Coefficients.Estimate("DayAhead") >= 0
                DayAhead_plausibel = "Nein";
            end
        end
        clear LinearesModell
    end
end

% Kenngrößen der einzelnen Standorte mitteln
Kennzahlen_mean = zeros(numel(Varianten),5);
for i = 1:numel(Zeitreihen)
    Kennzahlen_mean = Kennzahlen_mean + Kennzahlen(:,:,i);
end
Kennzahlen_mean = Kennzahlen_mean/(numel(Zeitreihen));
Bewertung = array2table(Kennzahlen_mean,'VariableNames',{'Variante','OrdinaryRsquared','AdjustedRsquared','MAPE','nRMSE'});
Bewertung.Variante = Varianten;

Bewertung_Standorte = struct;
for i = 1:numel(Zeitreihen)
    Bewertung_Standorte(i).Standort = Zeitreihen(i).Standort;
    Bewertung_Standorte(i).Bewertung_Varianten = array2table(Kennzahlen(:,:,i),'VariableNames',{'Variante','OrdinaryRsquared','AdjustedRsquared','MAPE','nRMSE'});
    Bewertung_Standorte(i).Bewertung_Varianten.Variante = Varianten;
end