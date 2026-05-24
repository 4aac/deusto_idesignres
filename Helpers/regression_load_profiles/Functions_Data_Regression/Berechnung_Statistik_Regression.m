function [Kennzahlen,Vergleich_Zeitreihen] = Berechnung_Statistik_Regression(Zeitreihen,Lineares_Modell,Variantenmodus,Time,data,data_fit,Sektor)
    
    Kennzahlen_Werte = zeros(numel(Zeitreihen),4);
    Bezeichnung(numel(Zeitreihen)+1,1) = "mean";
    Bezeichnung(numel(Zeitreihen)+2,1) = "median";
    
    % Generierung der synthetischen Lastprofil
    Vergleich_Zeitreihen = struct;
    for i = 1:numel(Zeitreihen)
        Predictors = Zeitreihen(i).Zeitreihe_normiert;
        Predictors_tbl = timetable2table(Predictors);
        measured = Zeitreihen(i).Zeitreihe_normiert.Lastgang;

        B = zeros(numel(Predictors_tbl.Betriebsruhe),1);
        for j = 1:numel(Predictors_tbl.Betriebsruhe)
            if Predictors_tbl.Betriebsruhe(j) == "false"
                B(j) = 0;
            else
                B(j) = 1;
            end
        end
        B = logical(B);
        B_inv = ~B;
        B_num = double(B);
        B_inv_num = double(B_inv);
        
        % Prüfen, ob Einzelmodelle oder Branchenmodell
        if numel(Lineares_Modell) > 1
            if Variantenmodus == "Betriebsruhe"
                Lastmodell.Normalbetrieb = Lineares_Modell(i).Normalbetrieb;
                Lastmodell.Betriebsruhe = Lineares_Modell(i).Betriebsruhe;
            elseif Variantenmodus == "Normalbetrieb"
                Lastmodell.Normalbetrieb = Lineares_Modell(i).Normalbetrieb;
            end
        else
            if Variantenmodus == "Betriebsruhe"
                Lastmodell.Normalbetrieb = Lineares_Modell.Normalbetrieb;
                Lastmodell.Betriebsruhe = Lineares_Modell.Betriebsruhe;
            elseif Variantenmodus == "Normalbetrieb"
                Lastmodell.Normalbetrieb = Lineares_Modell.Normalbetrieb;
            end
        end
        
        % Wenn Betriebsruhe berücksichtigt
        if Variantenmodus == "Betriebsruhe"
            predicted_N = predict(Lastmodell.Normalbetrieb,Predictors_tbl);
            predicted_B = predict(Lastmodell.Betriebsruhe,Predictors_tbl);
            predicted = predicted_N .* B_inv_num + predicted_B .* B_num;
            NumCoefficients = Lastmodell.Normalbetrieb.NumCoefficients;
        elseif Variantenmodus == "Normalbetrieb"
            predicted = predict(Lastmodell.Normalbetrieb,Predictors_tbl);
            NumCoefficients = Lastmodell.Normalbetrieb.NumCoefficients;
        end
    % Normierung angleichen
    switch Sektor
        case "Strom"
            NumObservations = numel(measured);
            size_yearly_val = numel(Time);
            Numyears = round(NumObservations/size_yearly_val);
            predicted_sum = sum(predicted);
            predicted = predicted.*(Numyears/predicted_sum)*4;
        case "Wärme"
            NumObservations = numel(measured);
            size_yearly_val = numel(Time);
            Numyears = round(NumObservations/size_yearly_val);
            predicted_sum = sum(predicted);
            predicted = predicted.*(Numyears/predicted_sum);
    end

    varNames = [data,data_fit];
    Vergleich_Zeitreihen(i).Standort = Zeitreihen(i).Standort;
    Vergleich_Zeitreihen(i).Zeitreihe_Vergleich = timetable(Predictors.Time,measured,predicted,'VariableNames',varNames);

    if any(strcmp('Fehldaten',Zeitreihen(i).Zeitreihe_normiert.Properties.VariableNames)==1)
            Fehldaten = Zeitreihen(i).Zeitreihe_normiert.Fehldaten;
            Vergleich_Zeitreihen(i).Zeitreihe_Vergleich.Fehldaten = Fehldaten;
            measured(Fehldaten==1,:) = [];
            NumObservations = numel(measured);
            predicted(Fehldaten==1,:) = [];
    end

    % Berechnung der statistischen Kenngrößen:

    % ordinary R squared:
    
    % für einfache lineare Regression
    % The total sum of squares
%     sum_of_squares = sum((measured-mean(measured)).^2);
%     % The sum of squares of residuals, also called the residual sum of squares:
%     sum_of_squares_of_residuals = sum((measured-predicted).^2);
%     % definition of the coefficient of correlation is
%     OrdinaryRsquared = 1 - sum_of_squares_of_residuals/sum_of_squares;

    % für multiple lineare Regression
    meas_mean = measured-mean(measured);
    pred_mean = predicted-mean(measured);
    sum_num = sum(meas_mean .* pred_mean)^2;
    sum_meas = sum(meas_mean.^2);
    sum_pred = sum(pred_mean.^2);
    OrdinaryRsquared = sum_num/(sum_meas*sum_pred);
    

    % adjusted R squared:
    AdjustedRsquared = OrdinaryRsquared - (NumCoefficients * (1 - OrdinaryRsquared))/(NumObservations - NumCoefficients - 1);
    Kennzahlen_Werte(i,2) = AdjustedRsquared;


    % MAPE - mean absolute percentage error:
    m = abs((measured-predicted)./(measured));
    MAPE = (1/NumObservations)*sum(m);

    % nRMSE - normalized root mean square error:
    % squared error
    SE = (measured-predicted).^2;
    % root mean square error
    RMSE = sqrt((1/NumObservations)*sum(SE));
    % normalized root mean square error
    nRMSE = RMSE / (max(measured)-min(measured));
    
    Kennzahlen_Werte(i,1) = OrdinaryRsquared;
    
    Kennzahlen_Werte(i,3) = MAPE;
    Kennzahlen_Werte(i,4) = nRMSE;
    Bezeichnung(i,1) = num2str(Zeitreihen(i).Standort);
    end

    Kennzahlen_mean = mean(Kennzahlen_Werte,1);
    Kennzahlen_median = median(Kennzahlen_Werte,1);
    Kennzahlen_ges = cat(1,Kennzahlen_Werte,Kennzahlen_mean,Kennzahlen_median);
    Kennzahlen_tbl = array2table(Kennzahlen_ges,'VariableNames',{'OrdinaryRsquared','AdjustedRsquared','MAPE','nRMSE'});
    Beschriftung_tbl = array2table(Bezeichnung,'VariableNames',{'Standort'});

    Kennzahlen = [Beschriftung_tbl Kennzahlen_tbl];
end


    