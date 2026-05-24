function [Kennzahlen,Vergleich_Zeitreihen] = Berechnung_Statistik_Synthese(Zeitreihen,Waerme_Modell,Time,data,data_fit)
    
    Kennzahlen_Werte = zeros(numel(Zeitreihen),3);
    Bezeichnung(numel(Zeitreihen)+1,1) = "mean";
    Bezeichnung(numel(Zeitreihen)+2,1) = "median";
    
    % Generierung der synthetischen Lastprofil
    Vergleich_Zeitreihen = struct;
    for i = 1:numel(Zeitreihen)
        Predictors = Zeitreihen(i).Zeitreihe_normiert;
        measured = Zeitreihen(i).Zeitreihe_normiert.Lastgang;
        NumObservations = numel(measured);
        size_yearly_val = numel(Time);
        Numyears = round(NumObservations/size_yearly_val);

        % Prüfen, ob Einzelmodelle oder Branchenmodell
        if numel(Waerme_Modell) > 1
            predicted_tbl = Berechnung_Waermezeitreihe_synthetisch(Predictors.Time,1000,Predictors.Temperatur,Predictors.Tagtyp_1_7,i,Waerme_Modell,Waerme_Modell);
            predicted = predicted_tbl.Waerme/(sum(predicted_tbl.Waerme)/Numyears);
        else
            predicted_tbl = Berechnung_Waermezeitreihe_synthetisch(Predictors.Time,1000,Predictors.Temperatur,Predictors.Tagtyp_1_7,1,Waerme_Modell,Waerme_Modell);
            predicted = predicted_tbl.Waerme/sum(predicted_tbl.Waerme/Numyears);
        end

    % Normierung angleichen
    NumObservations = numel(measured);
    size_yearly_val = numel(Time);
    Numyears = round(NumObservations/size_yearly_val);
    predicted_sum = sum(predicted);
    predicted = predicted.*(Numyears/predicted_sum);

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
    NumObservations = numel(measured);
    NumCoefficients = 8; % Temperatur: 1, Wochentage: 7
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


    