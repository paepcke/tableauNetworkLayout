#!/usr/bin/env python
'''
Created on Nov 18, 2017

@author: paepcke
Uses:
  https://networkx.github.io/documentation/networkx-1.9/reference/generated/networkx.drawing.layout.spring_layout.html
Inputs to graph constructor:
  d = {0: {1: {'weight':1}}} # dict-of-dicts single edge (0,1)
    
'''
import argparse
import collections
import csv
import os
import random
import sys
import networkx as nx

class Networker(collections.MutableMapping):
    '''
    Expects two files:
       - nodex.csv: first line is list of properties. Names and
           number of properties is arbitrary. First column must
           be a unique node identifier; anything hashable, such
           as integer or string. Use double quotes to escape
           commas, if needed. Or use another delimiter, and specify
           it from the command line.
           Example:
           
            nodeID,role,dob 
            user1,instructor,1982-9-4
            user2,student,2005-10-1
    '''
    
    def __init__(self, nodes_file,
                       links_file, 
                       columns=[0], 
                       delimiter=','
                       ):

        '''
        Constructor
        
        @param node_file:
        @type node_file:
        @param columns:
        @type columns:
        @param delimiter:
        @type delimiter:
        '''
        
        super(Networker, self).__init__()
        
        # Ensure both input files are there, and
        # are readable
        with open(nodes_file, 'r') as fd:  #@UnusedVariable
            pass
        with open(links_file, 'r') as fd:  #@UnusedVariable
            pass
    
        self.nodes_file = nodes_file
        self.links_file = links_file
        self.delimiter = delimiter
        
        self.node_property_name = None
        self.src_property_name  = None
        self.dst_property_name  = None
        
        
        (self.links_dict,self.nodes_dict) = self.import_inputs()
        self.flatten_link_table(self.links_dict)
        
    # ------------------------- Output in Various Forms --------------
            
    #-----------------------------
    # export_converted_input 
    #-----------------------    
            
    def export_converted_input(self, outfile):
        '''
        Output a copy of the input file, with all
        nodes replaced by their zip codes. Example:
        Each line of the form:
        
          node1,father_of,node2
        
        is turned into:
        
          zipcode1,father_of,zipcode2
        
        @param outfile: full path to output file
        @type outfile: str
        '''

        coded_source = []
        with open(self.node_file) as source_fd:
            nodes_file_reader = csv.reader(source_fd,
                                           delimiter=self.delimiter,
                                           quotechar='"')
            # Copy header unchanged, if present:
            if self.first_line_is_col_header:
                coded_source.append(nodes_file_reader.next())
                
            for source_line in nodes_file_reader: 
                for col in self.columns:
                    source_line[col] = self.node_to_zipcode[source_line[col]]
                coded_source.append(source_line)
                
        with open(outfile, 'w') as out_fd:
            nodes_file_writer = csv.writer(out_fd,
                                           delimiter=self.delimiter,
                                           quotechar='"')
            nodes_file_writer.writerows(coded_source)
            
        # Export second table mapping zipcodes to lat/long:
        geo_outputfile = os.path.splitext(outfile)[0] + '_geo.csv'
        with open(geo_outputfile, 'w') as geo_fd:
            geo_writer = csv.writer(geo_fd,
                                    delimiter=self.delimiter,
                                    quotechar='"')
            geo_writer.writerow(['zipcode', 'latitude', 'longitude'])
            for zipcode in self.zipcodes:
                geo_writer.writerow([zipcode,
                                     self.zipcodes[zipcode]['lat'],
                                     self.zipcodes[zipcode]['long']])

    #-----------------------------
    # get_overlay_reverser
    #-----------------------    
    
    def get_overlay_reverser(self):
        return Networker.OverlayReverser(self.zipcode_to_node)

    # ------------------------- Computations --------------
    
    #-----------------------------
    # import_inputs
    #-----------------------    
        
    def import_inputs(self):
        '''
        Given the node file and link file, create a
        structure like this:
        
        d = {'itk9yewjclq6bu' : {'gt38kh0h8oo' : {
                                    'weight' : 1.0,
                                    'type'   : 'responds_to'}
                                 },
             'itl3pttnro646k' : {'gx8ijxirqgy3ln' : {
                                    'weight' : 6.0,
                                    'type'   : 'responds_to'}},
             'itk9yewjclq6bu' : {'itezjr7i18ahx' : {
                                    'weight' : '4.0',
                                    'type'   : 'upvotes'}}
             }
             
        Also: set instance variables:
        
        	   	self.node_property_name
        	   	self.src_property_name
        	   	self.dst_property_name
        	   	
        	from information found in the input files.
        
        First, input nodes file, and create dicts with each node's properties.
        Then input links and complete this datastructure.
        
        The nodes properties input file is like this:
        
            nodeID,role,dob 
            user1,instructor,1982-9-4
            user2,student,2005-10-1
                ...
        
        where the first line lists properties. Names of
        the properties are arbitrary.
        
        The links input nodes file is like this:
        
            src,dst,weight,role
            itk9yewjclq6bu,gt38kh0h8oo,1.0,responds_to
            itl3pttnro646k,gx8ijxirqgy3ln,6.0,responds_to
                ...
        
        @return: tuple of two dicts:
                     {'node1' : {prop1 : prop1Val,
                                 prop2 : prop2Val},
                      'node2' : {prop1 : prop1Val,
                                 prop2 : prop2Val}
                     }
                 and the one above.
          
        '''
        with open(self.nodes_file, 'r') as node_fd:
            nodes_file_reader = csv.reader(node_fd, delimiter=self.delimiter)
            # Get node properties:
            node_property_names = nodes_file_reader.next()
            
            all_nodes_dict = {}

            # Pull in all node input lines:
            # Every line in the input may have 
            # multiple property columns:
            for node_info in nodes_file_reader:
                # Get the node name:
                node_name = node_info[0]
                properties_dict = {}
                
                for (property_name, property_val) in zip(node_property_names[1:], node_info[1:]):
                    properties_dict[property_name] = property_val
                    
                # Note: if nodes are repeated in the input file,
                # the latest will win:
                all_nodes_dict[node_name] = properties_dict
        
        with open(self.links_file, 'r') as link_fd:
            links_file_reader = csv.reader(link_fd, delimiter=self.delimiter)
            # Get link properties:
            link_property_names = links_file_reader.next()
            
            all_links_dict = {}
            
            for link_info in links_file_reader:
                # Get the end points:
                src_node_name = link_info[0]
                dst_node_name = link_info[1]

                # Link properties:
                properties_dict = {}
                
                for (property_name, property_val) in zip(link_property_names[2:], link_info[2:]):
                    properties_dict[property_name] = property_val

                all_links_dict[src_node_name] = {dst_node_name : properties_dict}

        return (all_links_dict, all_nodes_dict)

                
            
                
            
        
        
        
        
    #-----------------------------
    # get_next_nodes
    #-----------------------    
        
    def get_next_node(self, nodes_file_reader):
        if self.first_line_is_col_header:
            # Nodes file's first line are the column
            # headers. Discard them:
            nodes_file_reader.next()
        for source_line in nodes_file_reader: 
            for col in self.columns:
                try:
                    yield source_line[col]
                except IndexError:
                    raise ValueError("At least one column number in %s is beyond width of source file %s" %\
                                      (self.columns, self.node_file))
    
    #-----------------------------
    # get_next_zipcode 
    #-----------------------    
        
    def get_next_zipcode(self):
        '''
        Return a random zip code from
        a randomly chosen US state. Ensure
        that successive calls never return
        the same zip code.
        '''
        # Pick a random US state:
        rand_us_state       = random.choice(self.state_zips.keys())
        # Pick a random zip code within that state:
        rand_zip_from_state = random.choice(self.state_zips[rand_us_state])
        # Ensure that each zip code is only used once:
        self.state_zips[rand_us_state].remove(rand_zip_from_state)
        # If we used all of this state's zipcodes, remove
        # the state from consideration:
        if len(self.state_zips[rand_us_state]) == 0:
            del self.state_zips[rand_us_state]
            # If this was the last state at our disposal,
            # complain:
            if len(self.state_zips.keys()) == 0:
                raise ValueError("Not enough zipcodes in the US to cover this dataset.")
        return rand_zip_from_state

    #-----------------------------
    # internalize_zipcodes
    #-----------------------    

    def internalize_zipcodes(self):
        '''
        Read all zip codes from file into memory.
        Build three dicts: 
            self.zipcodes: {'state'  : ...,
                            'county' : ...,
                            'lat'    : ...,
                            'long'   : ...
                            }
            self.county_zips: {county : [zip1,zip2,...]}
            self.state_zips:  {state  : [zip1,zip2,...]}
        '''
        with open(Networker.ZIPCODE_SOURCE) as source_fd:
            reader = csv.reader(source_fd,
                                delimiter=self.delimiter,
                                quotechar='"')
            # Discard header of zip codes dataset:
            reader.next()
            for line in reader:
                the_zip   = line[Networker.ZIP_INDEX]
                zip_type  = line[Networker.ZIP_TYPE]
                if zip_type == 'MILITARY':
                    # No lat/long for military zip codes:
                    continue
                state     = line[Networker.STATE_INDEX]
                county    = line[Networker.COUNTY_INDEX]
                lat       = line[Networker.LAT_INDEX]
                longitute = line[Networker.LONG_INDEX]
                
                self.zipcodes[the_zip] = {'state' : state,
                                          'county' : county,
                                          'lat' : lat,
                                          'long' : longitute
                                          }  
                try:
                    self.county_zips[county].append(the_zip)
                except KeyError:
                    self.county_zips[county] = [the_zip]
                    
                try:
                    self.state_zips[state].append(the_zip)
                except KeyError:
                    self.state_zips[state] = [the_zip]
                
        self.all_zipcodes = self.zipcodes.keys()

    # --------- Dict Capabilities -----------
        
    def __getitem__(self, key):
        return self.node_to_zipcode[key]

    def __setitem__(self, key, value):
        raise NotImplemented("Zip overlays are read-only")

    def __delitem__(self, key):
        raise NotImplemented("Zip overlays are read-only")            

    def __iter__(self, zipOrNode='node'):
        return iter(self.node_to_zipcode)

    def __len__(self, zipOrNode='node'):
        return len(self.node_to_zipcode)

    def __keytransform__(self, key):
        return key
    
# ---------------------------- OverlayReverse -----------    

    class OverlayReverser(collections.MutableMapping):
        '''
        Dictionary to complement an instance of 
        Networker. Provides zipcode-to-node
        conversion.
        
        Not intended for direct instantiation.
        Instantiated via Networker.get_reverse_dict()
        '''
        
        def __init__(self, zipToNodeDict):
    
            super(Networker.OverlayReverser, self).__init__()
            self.zip_to_node = zipToNodeDict
                
        def __getitem__(self, key):
            return self.zip_to_node[key]
    
        def __setitem__(self, key, value):
            raise NotImplemented("Zip overlays are read-only")
    
        def __delitem__(self, key):
            raise NotImplemented("Zip overlays are read-only")            
    
        def __iter__(self):
            return iter(self.zip_to_node)
    
        def __len__(self):
            return len(self.zip_to_node)            
    
        def __keytransform__(self, key):
            return key



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--delimiter',
                        help='Column delimiter; default: ","',
                        default=',')
    parser.add_argument('-o', '--outfile',
                        help='Full output CSV file name if result output desired.',
                        default=None)
    parser.add_argument('node_file',
                        help='Fully qualified name of file with nodes and their properties.',
                        default=None)
    parser.add_argument('edge_file',
                        help='Fully qualified name of file with edges and their properties.',
                        default=None)
    args = parser.parse_args();
    networker = Networker(args.node_file,
                          args.edge_file,
                          delimiter=args.delimiter
                          )

    if args.outfile is not None:
        networker.export_converted_input(args.outfile)