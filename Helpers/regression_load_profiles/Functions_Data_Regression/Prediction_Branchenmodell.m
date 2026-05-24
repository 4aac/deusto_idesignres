function [Predicted] = Prediction_Branchenmodell(Modell,Predictors)
    NumPredictors = Modell.NumPredictors;
    Variables = string(Modell.PredictorNames);
    Coefficients = Modell.Coefficients;
    Predicted_Matrix = zeros(numel(Predictors.Time),(NumPredictors+1));
    Predicted_Matrix(1:end,1) = Coefficients.Estimate(1);

    varNames(1) = "intercept";
    Formula_1 = append("@(",varNames(1),",");
    str1 = string(Modell.Formula(4:end));
    str2 = varNames(1);
    Formula_2 = append(str2," +",str1);

    Predictors_VariableNames = string(Predictors.Properties.VariableNames);
    Coefficients_str = string(Coefficients.Properties.RowNames);
    
    
    for i = 1:NumPredictors
        k = find(Predictors_VariableNames==Variables(i));
        varNames(i+1) = Variables(i);

        %var = table2array(removevars(Predictors(:,k),"Time"));
        var = table2array(Predictors(:,k));

        if isa(var,'double')
            index_coeff = find(Coefficients_str==Variables(i));
            Predicted_Matrix(:,i+1) = var * Coefficients.Estimate(index_coeff);

        elseif isa(var,'categorical')
            var_rowname = append(Variables(i),"_",string(var));
            for j = 1:numel(var)
                if find(Coefficients_str==var_rowname(j))
                    index_coeff = find(Coefficients_str==var_rowname(j));
                    Predicted_Matrix(j,i+1) = Coefficients.Estimate(index_coeff);
                else
                    Predicted_Matrix(j,i+1) = 0;
                end
            end
        end
    end

    if (numel(varNames)-1) < NumPredictors
        error("Mindestens eine Eingangsvariable fehlt!");
    end
    Predicted_tbl = array2table(Predicted_Matrix,'VariableNames',varNames);

    for i = 2:numel(varNames)
        if i < numel(varNames)
            Formula_1 = append(Formula_1,varNames(i),",");
        else
            Formula_1 = append(Formula_1,varNames(i),")");
        end
    end 
    Formula = append(Formula_1,Formula_2);
    synth_func = str2func(Formula);
    Predicted = rowfun(synth_func,Predicted_tbl,'OutputVariableNames',"Lastprofil");
    Predicted = table2array(Predicted);
end