function Lastprofil_synth = Synthetisierung_Lastprofil(Modell,Predictors)
    % Umwandeln der Prädiktoren in table:
    Predictors_tbl = timetable2table(Predictors);
    
    if isfield(Modell,'Betriebsruhe')
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
            Lastprofil_Normalbetrieb = Prediction_Branchenmodell(Modell.Normalbetrieb,Predictors_tbl);
            Lastprofil_Betriebsruhe = Prediction_Branchenmodell(Modell.Betriebsruhe,Predictors_tbl);
            Lastprofil_synth = Lastprofil_Normalbetrieb.*B_inv_num + Lastprofil_Betriebsruhe.*B_num;
    else
        Lastprofil_synth = Prediction_Branchenmodell(Modell.Normalbetrieb,Predictors_tbl); 
    end
end