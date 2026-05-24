function [Zeitreihen_Vergleich] = Vergleich_Zeitreihen(Zeitreihen_Rohdaten_vs_Einzelmodelle,Zeitreihen_Rohdaten_vs_Branchenmodell)
Zeitreihen_Vergleich = struct;

for i = 1:numel(Zeitreihen_Rohdaten_vs_Einzelmodelle)
    Zeitreihen_Vergleich(i).Standort = Zeitreihen_Rohdaten_vs_Einzelmodelle(i).Standort;
    Zeitreihen_Vergleich(i).Zeitreihen_Vergleich = Zeitreihen_Rohdaten_vs_Einzelmodelle(i).Zeitreihe_Vergleich;
    Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Branchenmodell = Zeitreihen_Rohdaten_vs_Branchenmodell(i).Zeitreihe_Vergleich.Branchenmodell;
    Zeitreihen_Vergleich(i).Zeitreihen_Vergleich(Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Fehldaten,:) = [];
    figure

    % Create axes
    axes1 = axes('Parent',figure);
    hold(axes1,'on');
    
    % Create multiple line objects using matrix input to plot
    Time = Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Time;
    Rohlastgang = Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Rohlastgang;
    Einzel = Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Einzelmodell;
    Branche = Zeitreihen_Vergleich(i).Zeitreihen_Vergleich.Branchenmodell;
    YMatrix = cat(2,Rohlastgang,Einzel,Branche);

    plot1 = plot(Time,YMatrix,'Parent',axes1);
    set(plot1(1),'DisplayName','Rohlastgang');
    set(plot1(2),'DisplayName','Einzelmodell');
    set(plot1(3),'DisplayName','Branchenmodell','Color',[0 0.498039215803146 0]);

    % Create title
    str1 = "Vergleich Rohlastgang vs. Einzelmodell vs. Branchenmodell für Standort ";
    str2 = num2str(Zeitreihen_Vergleich(i).Standort);
    str3 = append(str1,str2);
    str3 = char(str3);
    title(str3);

    % Uncomment the following line to preserve the X-limits of the axes
    max_yval = max(YMatrix,[],'all')*1.1;
    ylim(axes1,[0 max_yval]);
    
    box(axes1,'on');
    hold(axes1,'off');

    % Create legend
    legend(axes1,'show');
end
end