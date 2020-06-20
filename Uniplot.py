import math
import os
import pandas as pd
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go

yList = []  # list of columns for Y-Axis (contain 'count' in type and should be numeric)
xList = []  # list of columns for X-Axis (not contain 'count' in type)
groupList = []  # list of columns for grouping (Primary key if unique values less 25)
yCountList = []  # list of columns non Numerical or Primary key with more 25 unique values
timeColumn = []  # list of columns (actually only one column) for Time X-Axis
# here is parsing column names function or manual set for each Lists
# and then function that make an array of Plot

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

    def getValues(self):
        # get values from  plot
        return self.x, self.y, self.group, self.detailed, self.detailedCol, self.typePlot, \
               self.aggregation, self.orientation


def groupDataframe(df, groupList, yAxis, aggregation, flag=False):
    # function for group dataframe by groupList and calculate aggregation function
    if flag or aggregation == 'top10count' or aggregation == 'count':
        df2 = df.copy()
        if aggregation != 'top10count' and aggregation != 'count':  # only for flag
            df2.loc[(df2[
                         yAxis] < 0), yAxis] = 0  # for correct sorting of bars (on bar chart) we need replace all FLAG values to 0
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
    if aggregation == '':  # for Scatter plot
        dfResult = df2.copy()
    return dfResult


def dfDetailedProcessing(dfPlot, detailedCol, detailed):
    # processed detailed graphs (when we want to use only one category per graph)
    if detailedCol == '':
        return dfPlot
    else:
        return dfPlot[dfPlot[detailedCol].isin(detailed)].copy()

def plotlyGraph(dfPlot, plots, plotSetting):
    # plot all graphs base on plots array
    # interactive plots
    # detailed (for value) and detailedCol (for detailed name column)
    # plot detailed graphs by each member of hue list (if we have more than 1 in hue list, except '') #### May be need make stacked bars instead
    addNumber = plotSetting["addNumber"]
    needSave = plotSetting["needSave"]
    addAnnot = plotSetting["addAnnot"]
    oneAxis = plotSetting["oneAxis"]
    categorAxis = plotSetting["categorAxis"]
    lineToBar = plotSetting["lineToBar"]

    # list of color for graph for consistant display category, we have not more 25 lines on one graph. So, 25 color should be enough
    colorList = ['Blue', 'Grey', 'DarkRed', 'Black', 'GoldenRod', \
                 'Red', 'MediumTurquoise', 'DarkOrchid ', \
                 'Peru', 'RosyBrown', 'Aqua', 'Yellow', 'Silver', \
                 'Khaki', 'DarkOliveGreen', 'DarkViolet', 'Coral', 'DeepPink', \
                 'Green', 'HotPink', 'LightSalmon', 'LightGray', 'MidnightBlue', \
                 'YellowGreen ', 'SpringGreen', 'Indigo ', 'LightBlue', 'LightSkyBlue',\
                 'Magenta']
    # count grid size to fit all graphs on one page
    numberPlot = len(plots)
    if len(plots) > 1:
        cols = 2
        # if we use subplots then plotly displays one legend for all plots,    for now not show legend if we have more than 1
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

    # create dictionary for maxY of each column Y axis
    dicMaxY = dict()

    # iterate all plot in plots[] to prepare plot titles
    for curPlot in range(0, numberPlot):
        x, y, group, detailed, detailedCol, typePlot, aggregation, orientation = plots[curPlot].getValues()

        # add number to title of graph, starting from 1 for human usability
        if addNumber: numPlot = str(curPlot + 1) + '. '
        else: numPlot = ''
        if group == '':
            if aggregation.lower().find('top10') != -1:
                strHue.append(numPlot + 'TOP10 ' + x)
            else:
                strHue.append(numPlot + y)
        else:
            if detailedCol == '':
                strHue.append(numPlot + y + " by " + group)
            else:
                if len(detailed) > 2:                   # use this limits for better displaying
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
    # default format for X axis, if we have numerical and non-numerical values plotly displays weird
    typeX = '-'
    for rPlot in range(1, rows + 1):
        for cPlot in range(1, cols + 1):
            if curPlot < numberPlot:
                x, y, group, detailed, detailedCol, typePlot, aggregation,  orientation = plots[curPlot].getValues()
                maxY = 0
                if group != '':
                # make a list of unique values of group column
                #     if detailedCol == '':
                #         listHue = dfPlot[group].unique()
                #     else:
                #         listHue = dfPlot[dfPlot[detailedCol].isin(detailed)][group].unique()
                # make a sorted list of hue (for consistence of colors)
                #     if typePlot != 'Scatter':
                    # when we sort Bar Chart data we lost order of category and have a different colors on different plots for the same category, dfUnique keep original (by hue names) order
                    arrUnique = dfPlot[group].unique()
                    dfUnique = pd.DataFrame(data=arrUnique, columns=[group]).sort_values(group).reset_index()
                    # group by dataframe and sorting by y value for visualisation purpose
                    dfPlotSort = groupDataframe(dfPlot, group, y, aggregation, True) # True is for not ignore 0 and -6, in other case we confusing in category colors
                    dfPlotSort = dfPlotSort.sort_values(by=y, ascending=False).reset_index().copy()
                    listHue = dfPlotSort[group]

                    # if we have a few category for grouping we need prepare data for each grouping category and plot line by line
                    if len(groupList) > 1: ### >2 ???
                        # if x and group member are the same name then grouping by one column
                        if x == group:
                            groupByList = [x]
                        else:
                            groupByList = [x, group]
                        # processing detailed graphs
                        dfPlot2 = dfDetailedProcessing(dfPlot, detailedCol, detailed)
                        dfGroupPlot = groupDataframe(dfPlot2, groupByList, y, aggregation)

                    else:
                        dfGroupPlot = dfPlot.copy()
                    # add each item from hue (category) to one graph
                    for iLine in range(0, len(listHue)):
                        df_xy = dfGroupPlot[dfGroupPlot[group] == listHue[iLine]][[x, y]].reset_index(drop=True).copy()
                        # sum result for Bar Chart for each member category (in other case graph is broken)
                        if typePlot == 'Bar Chart' and aggregation != 'count': #??? use groupDataframe twice (dfGroupPlot and df_xy)
                            df_xy = groupDataframe(df_xy, x, y, aggregation)
                        df_x = df_xy[x]
                        df_y = df_xy[y]
                        # get index of current category before sorting for consistent colors
                        # if typePlot != 'Scatter':
                        colorIndex = dfUnique[dfUnique[group] == listHue[iLine]].index
                        if typePlot != 'Histogram': # we don't use maxY for Histogram
                            curMaxY = df_xy[y].max()
                            if maxY < curMaxY: maxY = curMaxY
                        name = str(listHue[iLine])
                        if x == group:
                            ### make text list and rounding values for correct displaying
                            if aggregation == 'mean':
                                text = str(round(df_xy[y].mean(), 1))
                            if aggregation == 'sum':
                                if df_xy[y].sum() > 1: text = str(df_xy[y].sum().round(1))
                                else: text = str(df_xy[y].sum())
                            if aggregation == 'count' or aggregation.lower().find('top10') != -1:
                                if len(df_xy) > 0: text = str(df_xy[y][0])
                            ###
                        else:
                            text = name

                        if len(df_xy) > 0:
                            curColor = colorList[colorIndex[0]]
                            trace, typeX, annotationIndex, categoryOrder = getTrace(typePlot, df_x, df_y,
                                                                          name, text, curColor, categorAxis, lineToBar)
                            fig.add_trace(trace, row=rPlot, col=cPlot)

                            if typePlot == 'Scatter' or (typePlot == 'Line' and not lineToBar):
                                # add annotation only if we have more than 1 line on the plot
                                if len(listHue) > 1 and numberPlot > 1 and addAnnot:
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

                # Update xaxis and yaxis properties
                if aggregation in ['count', 'top10count']: yName = 'Count of ' + y
                else: yName = y

                if typePlot != 'Histogram':
                    fig.update_xaxes(title_text=x,
                                     row=rPlot,
                                     col=cPlot,
                                     categoryorder=categoryOrder,
                                     type=typeX)
                    fig.update_yaxes(title_text=yName,
                                     row=rPlot,
                                     col=cPlot,
                                     range=[0, maxY * 1.1]) # multiplication by 1.1 by experience for better displaying
                else:
                    fig.update_xaxes(title_text=yName,
                                     row=rPlot,
                                     col=cPlot)
            # add or update maxY
            if y not in dicMaxY.keys() or maxY > dicMaxY[y]:
                dicMaxY[y + "_" + typePlot] = maxY
            curPlot += 1

    if oneAxis:
        # update Y axis if oneAxis checked
        curPlot = 0
        for rPlot in range(1, rows + 1):
            for cPlot in range(1, cols + 1):
                if curPlot < numberPlot:
                    x, y, group, detailed, detailedCol, typePlot, aggregation,  orientation = plots[curPlot].getValues()
                    maxY = dicMaxY.get(y + "_" + typePlot)
                    if typePlot != 'Histogram':
                        fig.update_yaxes(row=rPlot,
                                         col=cPlot,
                                         range=[0, maxY * 1.1])
                curPlot += 1

    # add title = name of file / db table
    fig.update_layout(
        height=subplotHeight,
        title_text=os.path.basename(curTestData.path),
        showlegend=showlegend,
        barmode='group'
    )
    # save html and show OR just show in the web browser
    if needSave:
        if curTestData.type == 0:
            pathPlots = curTestData.path + "_plots.html"
        if curTestData.type == 1:
            pathPlots = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') + \
                        "/" + os.path.basename(curTestData.path) + "_plots.html"  # that's code for Mac OS only
        plotly.offline.plot(fig, filename=pathPlots)
    else:
        fig.show()

def getTrace(typePlot, df_x, df_y, name, text, curColor, categorAxis, lineToBar):
    # prepare trace for fig
    annotationIndex = 0
    categoryOrder = 'total descending'
    if typePlot == 'Histogram':
        trace = go.Histogram(x=df_y, name=name, marker_color=curColor
                                   # , histnorm='percent'
                                   # , xbins=dict(size=1)
                                   )
        typeX = '-'

    if typePlot == 'Scatter':
        trace = go.Scatter(x=df_x, y=df_y, mode="markers",
                        name=name, text=text, marker_color=curColor)
        typeX = '-'
        annotationIndex = df_y.idxmax()

    if typePlot == 'Line':
        if lineToBar:
            trace = go.Bar(x=df_x, y=df_y, name=name, text=text,
                           textposition='auto', marker_color=curColor)
        else:
            trace = go.Scatter(x=df_x, y=df_y, mode="lines",
                            name=name, text=text, line=dict(color=curColor))
        if categorAxis:
            typeX = 'category'
            categoryOrder = 'category ascending'
        else:
            typeX = 'date'

    if typePlot == 'Bar Chart':
        trace = go.Bar(x=df_x, y=df_y, name=name, text=text,
                    textposition='auto', marker_color=curColor)
        typeX = 'category'

    return trace, typeX, annotationIndex, categoryOrder
