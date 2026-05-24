function Branchenmodell = Anonymisierung_Branchenmodell(Modell)
    
    % Hier werden nur die Werte in das finale Branchenmodell eingetragen,
    % die wirklich für die Synthetisierung notwendig sind
    Branchenmodell.V_M_Buero_Produktion = Modell.V_M_Buero_Produktion;
    Branchenmodell.V_JV_M_Buero = Modell.V_JV_M_Buero;
    Branchenmodell.V_JV_M_Produktion = Modell.V_JV_M_Produktion;
    Branchenmodell.V_JV_F_Produktion = Modell.V_JV_F_Produktion;

    Coefficients = Modell.Normalbetrieb.Coefficients;
    Coefficients = removevars(Coefficients, ["SE","tStat","pValue"]);
    Branchenmodell.Normalbetrieb.Coefficients = Coefficients;

    Branchenmodell.Normalbetrieb.NumCoefficients = Modell.Normalbetrieb.NumCoefficients;
    Branchenmodell.Normalbetrieb.NumPredictors = Modell.Normalbetrieb.NumPredictors;
    Branchenmodell.Normalbetrieb.PredictorNames = Modell.Normalbetrieb.PredictorNames;
    Branchenmodell.Normalbetrieb.Formula = Modell.Normalbetrieb.Formula.LinearPredictor;
    
    if isfield(Modell,'Betriebsruhe')
        Branchenmodell.Betriebsruhe.Coefficients = Modell.Betriebsruhe.Coefficients;
        Branchenmodell.Betriebsruhe.NumCoefficients = Modell.Betriebsruhe.NumCoefficients;
        Branchenmodell.Betriebsruhe.NumPredictors = Modell.Betriebsruhe.NumPredictors;
        Branchenmodell.Betriebsruhe.PredictorNames = Modell.Betriebsruhe.PredictorNames;
        Branchenmodell.Betriebsruhe.Formula = Modell.Betriebsruhe.Formula.LinearPredictor;
    end
    
end