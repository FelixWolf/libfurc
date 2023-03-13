#!/usr/bin/env python3
from libfurc import fox5

LICENSE_FC_BY_SA = 0
LICENSE_FC0 = 1
LICENSE_FC_BY_NC_SA = 2
LICENSE_FC_ND_NC_SA = 3
LICENSE_FC_PRIVATE_SA = 4
LICENSE_FC_BY_X_SA = 5
LICENSE_DEP = 101

DEP_CS = "Dragon's Eye Productions/Catnip Studios"

def getSafeLicense(fro, to):
    #If license is compatible to be overwritten
    if fro in [LICENSE_FC0, None]:
        return to
    
    #Else, return the compatible license
    return fro

def reAttribute(fox,
                license = None, author = None,
                overwriteLicense = False,
                overwriteAuthor = False,
                overwriteLicenseForce = False
    ):
    #If author is a string, convert it to a list
    if type(author) == str:
        author = [author]
    
    for obj in fox.body:
        #If license is set but the object has no license, or overwriteLicense is set
        if license != None and (obj["License"] == None or overwriteLicense == True):
            obj["License"] = getSafeLicense(obj["License"], license)
        
        #If author is set
        if author != None:
            #And authors is none or empty
            if obj["Authors"] == None or len(obj["Authors"]) == 0 or overwriteAuthor == True:
                obj["Authors"] = author
            #Else, append the author
            else:
                obj["Authors"] = obj["Authors"] + author
        
        #If the license is DEP, ensure the DEP CS is in the Authors
        if license == LICENSE_DEP:
            #Only if it isn't in the authors table
            if obj["Authors"] == None:
                obj["Authors"] = [DEP_CS]
            else:
                obj["Authors"].append(DEP_CS)

def main():
    import argparse
    licensemap = {
        "FC-BY-SA": 0,
        "FC0": 1,
        "FC-BY-NC-SA": 2,
        "FC-ND-NC-SA": 3,
        "FC-PRIVATE-SA": 4,
        "FC-BY-X-SA": 5,
        "DEP": 101
    }
    
    parser = argparse.ArgumentParser(description='Reattribute a fox file')
    parser.add_argument('--license', help='Set license', choices = licensemap.keys(), default = None)
    parser.add_argument('--author', nargs="*", help='Set author (EG: --author "Vargskelethor"  "Fecal Funny Co.")', default = None,)
    
    parser.add_argument('--overwrite-author', action='store_true')
    parser.add_argument('--overwrite-license', action='store_true')
    parser.add_argument('--force-license', action='store_true')
    
    parser.add_argument('input', help='Input fox file')
    parser.add_argument('output', help='Output fox file', default = None)
    
    args = parser.parse_args()
    
    
    if args.output == None:
        args.output = args.input
    
    if args.license:
        args.license = licensemap[args.license]
    
    fox = fox5.load(args.input)

    reAttribute(fox, license = args.license, author = args.author,
                overwriteAuthor = args.overwrite_author,
                overwriteLicense = args.overwrite_license,
                overwriteLicenseForce = args.force_license
    )

    fox5.dump(fox, args.output)
    
if __name__ == "__main__":
    main()