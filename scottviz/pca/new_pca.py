__author__ = '2165430C'
import fileinput
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scottviz.settings")
from scottviz import settings
from msp.models import MSP
import sys
import numpy
import psycopg2 as pq
import mdp

outputLocation = settings.STATIC_PATH+'/csv/OutputMatrix.csv'

#README:
#No arguments will run the script without any filters
#If the first argument is 1, the script will treat every subsequent argument as a party filter (as per each party's id in the DB)
#Do not forget to edit the variable 'outputLocation' as necessary
#Do not forget to update DB details as necessary


def createQuery(query, filter):
    output = ""
    
    if query == "divisionCount":
        output = "SELECT MAX(id) FROM msp_division;"
        
    if query == "mspCount":
        output = "SELECT COUNT(DISTINCT id) FROM msp_msp;"

    if query == "votes":
        #No Filter
        if filter == 0:
            output = "SELECT msp.foreignid, div.id, vote.vote FROM msp_msp AS msp, msp_division AS div, msp_vote AS vote WHERE msp.id = vote.msp_id AND div.id= vote.division_id ORDER BY msp.foreignid"
            return output
        #Party Filter
        elif filter == 1:
            isFirst = 1
            count = -1
            output = "SELECT msp.foreignid, div.id, vote.vote FROM msp_msp AS msp, msp_division AS div, msp_vote AS vote WHERE msp.id = vote.msp_id AND div.id= vote.division_id "
            print "len(partyarguments): " + str(len(partyArguments))
            while count < len(partyArguments)-1:
                count = count + 1
                getDistinctParties(partyArguments[count])
                if isFirst == 1:
                    output = output + "AND (msp.party_id = " + partyArguments[count]
                    isFirst = 0
                else:
                    output = output + " OR msp.party_id = " + partyArguments[count]
            output = output + ") ORDER BY msp.foreignid"
            print "Output: " + output
        #Topic Filter
        elif filter == 2:
            isFirst = 1
            count = -1
            output = "SELECT msp.foreignid, div.id, vote.vote FROM msp_msp AS msp, msp_division AS div, msp_vote AS vote WHERE msp.id = vote.msp_id AND div.id= vote.division_id "
            print "len(topicarguments): " + str(len(topicArguments))
            while count < len(topicArguments)-1:
                count = count + 1
                if isFirst == 1:
                    output = output + "AND (div.topic_id = " + topicArguments[count]
                    isFirst = 0
                else:
                    output = output + " OR div.topic_id = " + topicArguments[count]
            output = output + ") ORDER BY msp.foreignid"
    
    if query == "msp":
        if filter == 0 or filter == 2:
            output = "SELECT msp.firstname, msp.lastname FROM msp_msp AS msp ORDER BY msp.foreignid"
            return output
        elif filter == 1:
            isFirst = 1
            count = -1
            output = "SELECT msp.firstname, msp.lastname FROM msp_msp AS msp "
            while count < len(partyArguments)-1:
                count = count + 1
                getDistinctParties(partyArguments[count])
                if isFirst == 1:
                    output = output + "WHERE (msp.party_id = " + partyArguments[count]
                    isFirst = 0
                else:
                    output = output + " OR msp.party_id = " + partyArguments[count]
            output = output + ") ORDER BY msp.foreignid"
    
    if query == "mspPartyList":
        if filter == 0 or filter == 2:
            output = "SELECT party.name FROM msp_party AS party, msp_msp AS msp WHERE msp.party_id = party.id ORDER BY msp.foreignid"
            return output
        elif filter == 1:
            isFirst = 1
            count = -1
            output = "SELECT party.name FROM msp_party AS party, msp_msp AS msp WHERE msp.party_id = party.id "
            while count < len(partyArguments)-1:
                count = count + 1
                getDistinctParties(partyArguments[count])
                if isFirst == 1:
                    output = output + "AND (msp.party_id = " + partyArguments[count]
                    isFirst = 0
                else:
                    output = output + " OR msp.party_id = " + partyArguments[count]
            output = output + ") ORDER BY msp.foreignid"
    return output

def getDistinctParties(cr,nameFromQuery):

    #Check if ID is a suitable value
    id =  cr.execute('SELECT name FROM msp_party WHERE id= %s', (nameFromQuery,))   #[party.name for party in Party.objects.filter(id=nameFromQuery)](0)
    try:
        idOutput = map(str, id)[0]
    except:
        print "Couldn't find PartyID: " + nameFromQuery + " in database - Are you sure you're passing the right value?"
       
    return nameFromQuery
    
def handleArguments(argList):
    global filter
    global partyArguments
    global topicArguments
    print argList
    argLength = len(argList)
    count = 1
    partyString = ''
    isFirst = 1

    if argLength == 1:
        filter = 0
        return
    if argList[1] == '1':
        filter = 1
        partyArguments = argList[2].split(",")
        print "PartyArgumentsinHandleArguments: " + str(partyArguments)
    elif argList[1] == '2':
        filter = 2
        topicArguments = argList[2].split(",")
        print "TopicArgumentsinHandleArguments: " + str(topicArguments)
    else:
        print "Invalid 1st Argument, running on full dataset. "
        print "Your 1st Argument was:" + argList[1]
        filter = 0

    
#Fills in values of 2D null matrix, with each entry being a vote (X=divisions, Y=MSPs)
def selectVotes(cr,matrix):
    result = cr.execute(createQuery("votes",filter))
    vote = cr.fetchall()
    count = -1
    for rows in vote:
        count += 1
        msp_entry = map(int, vote[count])[0]
        division_entry = map(int, vote[count])[1]
        vote_entry = map(int, vote[count])[2]
        try:
            matrix[msp_entry][division_entry] = vote_entry
        except:
            print "ERROR!!"
            print "MSP Entry: " + str(msp_entry)
            print "Division Entry: " + str(division_entry)
    print "1) Data has been retrieved from database."
    return matrix


def new_pca(parties, topics):
    data = {}
    filter = 0

    cn = pq.connect('dbname=m_14_pgtproja user=m_14_pgtproja password=pgtproja host=yacata.dcs.gla.ac.uk')
    cr = cn.cursor()

    handleArguments()

    result = cr.execute(createQuery("divisionCount", filter))
    maxDivision = cr.fetchone()
    result = cr.execute(createQuery("mspCount", filter))
    maxMSP = cr.fetchone()

    #Convert tuples to list of ints, extract the first (and only value)
    maxMSP_int = map(int, maxMSP)[0] + 1
    maxDivision_int = map(int, maxDivision)[0] + 1


    #Create null matrix (to be replaced with value wherever an msp voted on a division)
    matrix = numpy.zeros((int(maxMSP_int), int(maxDivision_int)))

    matrix = selectVotes()

    #Slightly hacky solution to removing null first row and column which exist as a bi-product of required matrix dimensions
    matrix = numpy.delete(matrix,(0),axis=0)
    matrix = numpy.delete(matrix,(0),axis=1)

    #Deletes every all-zero row in the input matrix (this is necessary for the filters to work correctly)
    matrix = matrix[~numpy.all(matrix == 0, axis=1)]

    numpy.savetxt("InputMatrix.csv", matrix, fmt="%s", delimiter=",")


    #PCA magic happens here using MDP
    imdp = mdp.nodes.PCANode(output_dim=2)
    output = imdp(matrix)

    #Ouput everything to CSV so as to be read by D3/Javascript
    numpy.savetxt(outputLocation, output, fmt="%s", delimiter=",")


    #Append name of party and MSP names(as a string) to each row of output text
    msps = MSP.objects.all().order_by('id')
    count = -1
    path = os.path.dirname(os.path.abspath(__file__)) + outputLocation
    firstLine = 0
    for line in fileinput.input(outputLocation, inplace=1):
        count += 1
        #If first line of csv add header, else append party name
        if firstLine == 0:
            print 'X,Y,Party,MSP Name'
            firstLine = 1;
        else:
            try:
                print '{0}{1}'.format(line.rstrip('\n'), (',' + str(msps[count].party) + ',' + str(msps[count])))
            except:
                pass
    print "done!"


