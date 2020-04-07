import math
import os
import pandas as pd
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class Plot(object):
    # class for keep info about plot
    def __init__(self, x, y, group, aggregation, detailed, detailedCol, typePlot, orientation='v'):
        self.x = x
        self.y = y
        self.group = group
        self.aggregation = aggregation
        self.detailed = detailed        # detailed list (for value) and detailedCol (for detailed name column)
        self.detailedCol = detailedCol  # plot detailed graphs by each member of hue list (if we have more than 1 in hue list, except '') #### May be need make stacked bars instead
        self.typePlot = typePlot
        self.orientation = orientation

def groupDataframe(self, df, groupList, yAxis, aggregation, flag=False):
    # function for group dataframe by groupList and calculate aggregation function
    if flag or aggregation == 'top10count' or aggregation == 'count':
        df2 = df.copy()
        if aggregation != 'top10count' and aggregation != 'count': # only for flag
            df2.loc[(df2[yAxis] < 0), yAxis] = 0 # for correct sorting of bars (on bar chart) we need replace all FLAG values to 0
                                                # but for top10count and count yAxis is not numerical field
    else:
        df2 = df[df[yAxis] > 0].copy()
    if aggregation == 'sum':
        dfResult = df2.groupby(groupList)[yAxis].sum().reset_index(name=yAxis).copy()
    if aggregation == 'mean':
        dfResult = df2.groupby(groupList)[yAxis].mean().reset_index(name=yAxis).copy()
    if aggregation == 'count':
        dfResult = df2.groupby(groupList)[yAxis].nunique().reset_index(name=yAxis).copy()
    if aggregation == 'top10count':
        dfResult = df2.groupby(groupList)[yAxis].nunique().reset_index(name=yAxis).nlargest(10, yAxis).copy()
    if aggregation == 'top10':
        dfResult = df2.groupby(groupList)[yAxis].sum().reset_index(name=yAxis).nlargest(10, yAxis).copy()
    if aggregation == '': # for Scatter plot
        dfResult = df2.copy()

    return dfResult

def dfDetailedProcessing(self, dfPlot, detailedCol, detailed):
    # if detailedCol != '' then leave only values in detailed
    if detailedCol == '':
        return dfPlot
    else:
        return dfPlot[dfPlot[detailedCol].isin(detailed)].copy()

def plotlyGraph(self, dfPlot, plots):
    # plot all graphs base on plots array
    # interactive plots
    # detailed (for value) and detailedCol (for detailed name column)
    # plot detailed graphs by each member of hue list (if we have more than 1 in hue list, except '') #### May be need make stacked bars instead

    # list of color for graph for consistant display category, we have not more 25 lines on one graph. So, 25 color should be enough
    colorList = ['Blue', 'Red', 'Green', 'GoldenRod', 'Black', \
                 'SpringGreen', 'MediumTurquoise', 'DarkOrchid ', \
                 'Peru', 'RosyBrown', 'Aqua', 'Yellow', 'Silver', \
                 'Khaki', 'DarkOliveGreen', 'DarkViolet', 'Coral', 'DeepPink', \
                 'Magenta', 'HotPink', 'LightSalmon', 'LightGray', 'MidnightBlue', \
                 'YellowGreen ', 'DarkRed ', 'Indigo ', 'LightBlue', 'LightSkyBlue ']
    # count grid size to fit all graphs on one page
    numberPlot = len(plots)
    if len(plots) > 1:
        cols = 2
        # if we use subplots plotly displays one legend for all plots,    for now not show legend if we have more than 1
        showlegend = False
    else:
        cols = 1
        showlegend = True
    rows = math.ceil(numberPlot / cols)
    if rows > 1:
        subplotHeight = rows * 400  # by experience
    else:
        subplotHeight = 550  # by experience

    # create a list of names on graphs
    strHue = []
    for curPlot in range(0, numberPlot):
        x = plots[curPlot].x
        y = plots[curPlot].y
        group = plots[curPlot].group
        detailed = plots[curPlot].detailed
        detailedCol = plots[curPlot].detailedCol
        aggregation = plots[curPlot].aggregation
        numPlot = str(curPlot + 1) + '. '  # starting from 1 for human usability
        if group == '':
            if aggregation.lower().find('top10') != -1:
                strHue.append(numPlot + 'TOP10 ' + x)
            else:
                strHue.append(numPlot + y)
        else:
            if detailedCol == '':
                strHue.append(numPlot + y + " by " + group)
            else:
                if len(detailed) > 3:  # use this limits for better displaying
                    strTemp = ' (Filtered) '
                else:
                    if detailedCol != group:
                        strTemp = " (" + str(detailedCol) + " = " + ", ".join(map(str, detailed)) + ")"
                    else:
                        strTemp = " (" + ", ".join(map(str, detailed)) + ")"
                strHue.append(numPlot + y + " by " + group + strTemp)

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=strHue)

    # plot numberPlot graphs in the loop
    curPlot = 0
    # default format for X axis, if we have numerical and non-numerical values plotly displays weird,
    # then need change to 'category' for Bar Chart
    typeX = '-'
    for rPlot in range(1, rows + 1):
        for cPlot in range(1, cols + 1):
            if curPlot < numberPlot:
                x = plots[curPlot].x
                y = plots[curPlot].y
                group = plots[curPlot].group
                detailed = plots[curPlot].detailed
                detailedCol = plots[curPlot].detailedCol
                typePlot = plots[curPlot].typePlot
                aggregation = plots[curPlot].aggregation
                orientation = plots[curPlot].orientation  # looks bad in horizontal plotly bars
                maxY = 0
                if group != '':
                    # make a list of unique values of group column
                    if detailedCol == '':
                        listHue = dfPlot[group].unique()
                    else:
                        listHue = dfPlot[dfPlot[detailedCol].isin(detailed)][group].unique()
                    # make a sorted list of hue (for Bar Chart and Line)
                    if typePlot == 'Bar Chart' or typePlot == 'Line':
                        # when we sort Bar Chart data we lost order of category and have a different colors on different plots for the same category, dfUnique keep original (by hue names) order
                        arrUnique = dfPlot[group].unique()
                        dfUnique = pd.DataFrame(data=arrUnique, columns=[group]).sort_values(group).reset_index()
                        # group by dataframe and sorting by y value for Bar Chart only for visualisation purpose
                        dfPlotSort = self.groupDataframe(dfPlot, group, y, aggregation,
                                                         True)  # True is for not ignore 0 and -6, in other case we confusing in category colors
                        dfPlotSort = dfPlotSort.sort_values(by=y, ascending=False).reset_index().copy()
                        listHue = dfPlotSort[group]

                    # if we have a few category for grouping we need prepare data for each grouping category and plot line by line
                    if len(self.groupList) > 1:  ### >2 ???
                        # if x and hue member are the same name grouping one column
                        if x == group:
                            groupByList = [x]
                        else:
                            groupByList = [x, group]
                        # processing detailed graphs
                        dfPlot2 = self.dfDetailedProcessing(dfPlot, detailedCol, detailed)
                        dfGroupPlot = self.groupDataframe(dfPlot2, groupByList, y, aggregation)

                    else:
                        dfGroupPlot = dfPlot.copy()
                    # add each item from hue (category) to one graph
                    for iLine in range(0, len(listHue)):
                        df_xy = dfGroupPlot[dfGroupPlot[group] == listHue[iLine]][[x, y]].reset_index(drop=True).copy()
                        # sum result for Bar Chart for each member category (in other case graph is broken)
                        if typePlot == 'Bar Chart' and aggregation != 'count':  # ??? use groupDataframe twice (dfGroupPlot and df_xy)
                            df_xy = self.groupDataframe(df_xy, x, y, aggregation)
                        # get index of current category before sorting for consistent colors
                        if typePlot == 'Bar Chart' or typePlot == 'Line':
                            colorIndex = dfUnique[dfUnique[group] == listHue[iLine]].index
                        df_x = df_xy[x]
                        df_y = df_xy[y]
                        if maxY < df_xy[y].max(): maxY = df_xy[y].max()
                        name = str(listHue[iLine])
                        if x == group:
                            ### make text list and rounding values for correct displaying
                            if aggregation == 'mean':
                                text = str(round(df_xy[y].mean(), 1))
                            if aggregation == 'sum':
                                if df_xy[y].sum() > 1:
                                    text = str(df_xy[y].sum().round(1))
                                else:
                                    text = str(df_xy[y].sum())
                            if aggregation == 'count' or aggregation.lower().find('top10') != -1:
                                if len(df_xy) > 0: text = str(df_xy[y][0])
                            ###
                        else:
                            text = name

                        if len(df_xy) > 0:
                            annotationIndex = 0
                            if typePlot == 'Scatter':
                                fig.add_scatter(x=df_x, y=df_y, mode="markers", row=rPlot, col=cPlot,
                                                name=name, text=text)
                                typeX = '-'
                                annotationIndex = df_xy[y].idxmax()

                            if typePlot == 'Line':
                                fig.add_scatter(x=df_x, y=df_y, mode="lines", row=rPlot, col=cPlot,
                                                name=name, text=text, line=dict(color=colorList[iLine]))
                                typeX = 'date'

                            if typePlot == 'Bar Chart':
                                fig.add_bar(x=df_x, y=df_y, row=rPlot, col=cPlot, name=name, text=text,
                                            textposition='auto', marker_color=colorList[colorIndex[0]])
                                typeX = 'category'

                            if typePlot == 'Scatter' or typePlot == 'Line':
                                # add annotation only if we have more than 1 line on the plot
                                if len(listHue) > 1 and numberPlot > 1:
                                    fig.add_annotation(
                                        go.layout.Annotation(
                                            x=str(df_x[annotationIndex]),
                                            y=str(df_y[annotationIndex]),
                                            xref="x" + str(curPlot + 1),
                                            yref="y" + str(curPlot + 1),
                                            text=name,
                                            showarrow=True,
                                            align="center",
                                            arrowhead=2,
                                            arrowsize=1,
                                        )
                                    )

                # if field for grouping is empty we are preparing a Dataframe grouping be x field
                else:
                    groupList = [x]
                    xIndexCol = dfPlot.columns.get_loc(x)

                    dfGroupPlot = self.groupDataframe(dfPlot, groupList, y, aggregation)

                    df_x = dfGroupPlot[x]
                    df_y = dfGroupPlot[y]
                    maxY = dfGroupPlot[y].max()
                    name = y
                    ### round values for better displaying
                    if aggregation in ('mean', 'sum'): dfGroupPlot = dfGroupPlot.round({y: 1})
                    text = dfGroupPlot[y]
                    ###
                    if len(dfGroupPlot) > 0:

                        if typePlot == 'Scatter':
                            fig.add_scatter(x=df_x, y=df_y, mode="markers", row=rPlot, col=cPlot,
                                            name=name, text=text)
                            typeX = '-'
                        if typePlot == 'Line':
                            fig.add_scatter(x=df_x, y=df_y, mode="lines", row=rPlot, col=cPlot,
                                            name=name, text=text, line=dict(color=colorList[0]))
                            typeX = 'date'
                        if typePlot == 'Bar Chart':
                            fig.add_bar(x=df_x, y=df_y, row=rPlot, col=cPlot, name=name, text=text,
                                        textposition='auto', marker_color=colorList[0])
                            typeX = 'category'

                # Update xaxis and yaxis properties
                yName = y
                if aggregation in ['count', 'top10count']: yName = 'Count of ' + y
                fig.update_xaxes(title_text=x,
                                 row=rPlot,
                                 col=cPlot,
                                 categoryorder='total descending',
                                 type=typeX)
                fig.update_yaxes(title_text=yName,
                                 row=rPlot,
                                 col=cPlot,
                                 range=[0, maxY * 1.1])  # multiplication by 1.1 by experience for better displaying

            curPlot += 1
    # add title = name of file / db table
    fig.update_layout(
        height=subplotHeight,
        title_text=os.path.basename(self.curTestData.path),
        showlegend=showlegend,
        barmode='group'
    )
    # save html and show OR just show in the web browser
    if self.savePlotsCheckbox.isChecked():
        if self.curTestData.type == 0:
            pathPlots = self.curTestData.path + "_plots.html"
        if self.curTestData.type == 1:
            pathPlots = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') + \
                        "/" + os.path.basename(self.curTestData.path) + "_plots.html"  # that's code for Mac OS only
        plotly.offline.plot(fig, filename=pathPlots)
    else:
        fig.show()