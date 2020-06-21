#!/usr/bin/python

# This file contains confidential information regarding the inner workings of
# DECADS which is property of SCONDAQ GmbH. Do not copy without express
# permission from either the SCONDAQ GmbH or the author (T. Ballance). This file
# is not to be distributed under any circumstances.
# Copyright Tim Ballance 2013

from array import *
from struct import *
import types
import StringIO


exponentsMetersIndex = 0
exponentsTimeIndex = 1
exponentsMassIndex = 2
exponentsTemperatureIndex = 3
exponentsCurrentIndex = 4

class physUnit():
    def __init__( self, exponents=None ):
    
        if( exponents is None ): # initialise an empty unit
            self.exponents = array( "d", [0]*8 )
            
        elif( type( exponents ) is array ): # initialise from an array
            assert len( exponents ) is 8, "physUnit initialised with array of length %r" % len( exponents )
            assert exponents.typecode is 'd', "physUnit initialised with units of %r instead of double" % exponents.typecode
            self.exponents = exponents
        
        elif( type( exponents ) is list ): # intialise from a list
            assert len( exponents ) < 9, "physUnit initialised with too long list %r" % len( exponents )
            
            self.exponents = array( "d", [0]*8 ) # initiliase the array
            for i in range( 0, len( exponents ) ):
                self.exponents[i] = exponents[i] # attempt to copy each element into the array
            
        elif( type( exponents ) is str ): # initialise from unit string

            # parse the string
            self.fromString( exponents )
        
        else:
            raise Exception( "Unrecognised unit init type: %r" % type( exponents ) )

    def __str__( self ):
        return "physUnit: " + repr( self.exponents.tolist() )

    def encode( self, stream ):
        stream.write( self.exponents.tostring() )

    @classmethod
    def decode( cls, stream ):
        exponents = array( "d" )
        # read in 8 doubles
        exponents.fromlist( list(unpack("8d", stream.read(64) ) ) ) 
        
        return cls( exponents )

    def fromString( self, string ):
        # set the units from a unit string
        assert type(string) is str, "physUnit.fromString called with NOT A STRING: %r" % type( string )
        
        # initialise to zero
        self.exponents = array( "d", [0]*8 )
        
        # check each character in the string
        i = 0
        while i < len(string):
            c = string[i]
            
            if( c == 'm' ): # symbol for meters
                self.exponents[ exponentsMetersIndex ] += 1
            
            elif( c == 's' ): # symbol for seconds
                self.exponents[ exponentsTimeIndex ] += 1
                
            elif( c == 'g' ): # symbol for kg
                self.exponents[ exponentsMassIndex ] += 1
                
            elif( c == 'K' ): # symbol for kelvin
                self.exponents[ exponentsTemperatureIndex ] += 1
                
            elif( c == 'A' ): # symbol for amps
                self.exponents[ exponentsCurrentIndex ] += 1
                
            elif( c == 'V' ): # symbol for volts
                # V = kg m^2 A^-1 s^-3
                self.exponents[ exponentsMassIndex ] += 1
                self.exponents[ exponentsMetersIndex ] += 2
                self.exponents[ exponentsCurrentIndex ] -= 1
                self.exponents[ exponentsTimeIndex ] -= 3

            elif( c == 'H' ): # start of symbol for Hz
                i += 1
                c = string[i]
                if c == 'z': # Hz
                    self.exponents[ exponentsTimeIndex ] -= 1
                else: # unrecognised
                    print "physUnit.fromString unrecognised unit: H", c, " in ", string
            
            else: # unrecognised
                print "physUnit.fromString unrecognised unit: ", c, " in ", string

            i += 1

    def __eq__( self, otherUnit ):
        if( otherUnit is None ):
            return self.__eq__( physUnit() )
        
        else:
            assert isinstance( otherUnit, physUnit ), "physUnit comparison with something other than physUnit"

            for i in range(0,7):
                if( self.exponents[i] != otherUnit.exponents[i] ):
                    return False
                
            return True
        
        
class dvmValue():
    def __init__( self, value=None, error=None, unit=None ):
        if( type( value ) is type( None ) ): # if we are given a blank value
            self.value = None
            self.error = None
        elif isinstance( value, dvmValue ):
            # If we have been given a dvmValue, copy it
            self.value = value.value
            self.unit = value.unit
            self.error = value.error

        else:

            try:
                float( value )
            except ValueError:
                print "dvmValue initialised with non-floatable value: %r" % type( value )
                raise

            self.value = float(value)
            
            if error is None:
                self.error = None
            else:
                try:
                    float( error )
                except ValueError:
                    print "dvmValue initialised with non-floatable error: %r" % type( error )
                    raise

                self.error = float(error)
        
        if( unit is None ):
            self.unit = None
        elif type(unit) is str:
            self.unit = physUnit( unit )
        else:
            assert isinstance( unit, physUnit ), "dvmValue initialised with wrong class unit"
            
            self.unit = unit

    def __str__( self ):
        outputString = "dvmValue: " + str( self.value ) + "g" 
        outputString = outputString + str( self.error ) + " " 
        outputString = outputString + str( self.unit )
        return outputString

    def encode( self, stream ):
    
        mask = 5 # start with default mask
        if( self.error is None ):
            mask = mask & ~1 # don't send error if it is null
        if( self.unit is None ):
            mask = mask & ~4 # don't send unit if it is null

        stream.write( pack( "B", mask ) ) # send mask
        stream.write( pack( "d", self.value ) ) # send value
        
        if( mask & 1 ): # if we should encode the error value
            stream.write( pack( "d", self.error ) ) # send error
            
        if( mask & 4 ): # if we should encode the unit
            self.unit.encode( stream ) # send unit

    @classmethod
    def decode( cls, stream ):
        # read in 1 byte of mask
        mask = unpack( "B", stream.read(1) )[0]
        
        # read in 1 double of value
        value = unpack( "d", stream.read(8) )[0]
        
        error = None 
        if( mask & 1 ): # if the error value is encoded
            # read in 1 double of error
            error = unpack( "d", stream.read(8) )[0]
            
        unit = None
        if( mask & 4 ): # if the unit is encoded
            # read in 1 physUnit
            unit = physUnit.decode( stream )

        return cls( value, error, unit )


class dvmList():
    def __init__( self, n=None, unit=None, values=None, errors=None ):
    
        if( n is None or n == 0 ): # initialise empty dvmList
            self.n = None
            self.values = None
            self.errors = None
            
        elif type(n) is list:   # If the first argument is a python list, init from it

            assert all( isinstance( x, (int, float) ) for x in n ), "dvmList initialised with list containing non-numerics: %r" % n
            
            self.n = len(n)
            self.values = n

            if( unit is None ):
                self.unit = None
            elif type(unit) is str:
                self.unit = physUnit( unit )
            else:
                assert isinstance( unit, physUnit ), "dvmList initialised with wrong class unit"
                self.unit = unit
            
            if( errors is None ):
                self.errors = None
            else:
                assert type( errors ) is list, "dvmList initialised with non-list errors list: %r" % type( errors ) 
                
                self.errors = errors

        else:
            assert type( n ) is int, "dvmList initialised with non-integer length: %r" % type( n )
            assert type( values ) is list or tuple, "dvmList initialised with non-list/tuple values list: %r" % type( values ) 
            assert all( isinstance( x, (int, float) ) for x in values ), "dvmList initialised with list containing non-numerics: %r" % n
            
            self.n = n
            self.values = values
        
            if( unit is None ):
                self.unit = None
            else:
                assert isinstance( unit, physUnit ), "dvmList initialised with wrong class unit"
                self.unit = unit
            
            if( errors is None ):
                self.errors = None
            else:
                assert type( errors ) is list, "dvmList initialised with non-list errors list: %r" % type( errors ) 
                
                self.errors = errors
        
    def encode( self, stream ):
        mask = 5 # start with default mask
        if( self.unit is None ):
            mask = mask & ~4 # don't send unit if it is null

        # work out what the mask should be
        if( self.errors is not None ):
            mask = mask | 1     
        if( self.unit is not None ):
            mask = mask | 4
        
        # send the mask
        stream.write( pack( "B", mask ) )
        
        # send the unit, if necessary
        if( self.unit is not None ):
            self.unit.encode( stream )
        
        # send uint32 size
        stream.write( pack( "I", self.n ) )
        
        # send every double value
        for i in range( 0, self.n ):
            stream.write( pack( "d", self.values[i] ) )
        
        # send every error value, if necessary
        if( self.errors is None ):
            errorList = [None]*self.n
        else:
            errorList = self.errors
        for i in range( 0, self.n ):
            if( errorList[i] is None ):
                stream.write( pack( "B", 0 ) ) # send null byte
            else:
                stream.write( pack( "B", 1 ) ) # send error indicator
                stream.write( pack( "d", errorList[i] ) ) # send the error
                
    @classmethod
    def decode( cls, stream ):
        # read the mask
        mask = unpack( "B", stream.read(1) )[0]

        # If the mask & 6 is true, then we are receiving a singleton list, which is parsed differently
        if( mask & 6 ):
            newValue = dvmValue.decode( stream )

            n = 1
            values = [ newValue.value ]
            errors = [ newValue.error ]
            unit = newValue.unit
            return cls( n, unit, values, errors )
        
        # Otherwise, treat it as a normal list
        if( mask & 4 ):
            # if bit 2 is set, then read in a unit
            unit = physUnit.decode( stream )
        else:
            unit = None
        
        # read in the length of the list
        n = unpack( "I", stream.read(4) )[0]

        # read in all the data values
        values = unpack( "%dd" % n, stream.read( n*8 ) )
        
        errors = None
        if( mask & 1 ):
            # if bit 0 is set, then read in errors
            errors = [ None ]*n
            for i in range( 0, n ):
                # for each element, the eMask determines if the error is sent
                eMask = unpack( "B", stream.read(1) )[0]
                if( eMask & 1 ):
                    # if the error has been sent, read it in
                    errors[i] = unpack( "d", stream.read(8) )[0]
        

        return cls( n, unit, values, errors )
    

    
    
# These constants are defined in Zipkes' hwiDLL.h
argType_int = 5
argType_double = 6
argType_dvmValue = 7
argType_string = 9
argType_dvmList = 10

        
class hwiArg():
    def __init__( self, cType=None, name=None, data=None ):

        if type( cType ) is None :  # arg is uninitialised
            self.cType = None
            self.name = "Uninitialised hwiArg"
            self.data = None
            return
            
        assert type( name ) is str, "hwiArg initialised without proper name type: %r" % type( name ) 
        assert len( name ) <= 64, "hwiArg initialised with an overlong name: %r" % len( name ) 
        
        self.name = name
        self.cType = cType
        
        if cType == argType_int:
            self.vInt = data
            
        elif cType == argType_double:
            self.vDouble = data
            
        elif cType == argType_string:
            self.vString = data
    
        elif cType == argType_dvmValue:
            if data is None:
                self.vDvmValue = dvmValue()
            else:
                assert isinstance( data, dvmValue ), "hwiArg-dvmValue initialised without proper dvmValue class"
                self.vDvmValue = data   

    
        elif cType == argType_dvmList:
            if data is None:
                self.vDvmList = dvmList()
            else:
                assert isinstance( data, dvmList ), "hwiArg-dvmList initialised without proper dvmList class"
    
            self.vDvmList = data
        
        else:
            print "Unrecognised cType: %r" % cType

    def __str__( self ):
        if self.cType == argType_int:
            typeStr = "int"            
        elif self.cType == argType_double:
            typeStr = "double"            
        elif self.cType == argType_string:
            typeStr = "string"            
        elif self.cType == argType_dvmValue:
            typeStr = "dvmValue"            
        elif self.cType == argType_dvmList:
            typeStr = "dvmList"                       
        else:
            print "Unrecognised cType: %r" % self.cType
            
        return "(" + typeStr + ") " + str( self.name )

    def encodeStructure( self, stream ):
        stream.write( pack( "B", self.cType ) )
        stream.write( pack( "64s", self.name ) )

    def encodeData( self, stream ):
        if self.cType == argType_int:
            stream.write( pack( "I", self.vInt ) )
            
        elif self.cType == argType_double:
            stream.write( pack( "d", self.vDouble ) )
            
        elif self.cType == argType_string:
            # first we encode the uint32 string length
            stream.write( pack( "I", len( self.vString ) ) )
            # then the string
            stream.write( self.vString )
            
        elif self.cType == argType_dvmValue:
            self.vDvmValue.encode( stream )
        
        elif self.cType == argType_dvmList:
            self.vDvmList.encode( stream )
        

    @classmethod
    def decodeStructure( cls, stream ):
        cType = unpack( "B", stream.read(1) )[0]
        rawName = unpack( "64s", stream.read(64) )[0]
        nullIndex = rawName.find('\0')
        name = rawName[ 0:nullIndex ]
        return cls( cType, name )

    def decodeData( self, stream ):
        
        if self.cType == argType_int:
            self.vInt = unpack( "I", stream.read(4) )[0]
            
        elif self.cType == argType_double:
            self.vDouble = unpack( "d", stream.read(8) )[0]
            
        elif self.cType == argType_string:
            # first we decode the uint32 string length
            length = unpack( "I", stream.read(4) )[0]
            # then the string
            self.vString = unpack( "%ds" % length, stream.read( length ) )[0]
            
        elif self.cType == argType_dvmValue:
            self.vDvmValue = dvmValue.decode( stream )
        
        elif self.cType == argType_dvmList:
            self.vDvmList = dvmList.decode( stream )

    def newDataInstanceFromStream( self, stream ):

        data = None
        
        if self.cType == argType_int:
            data = unpack( "I", stream.read(4) )[0]         
        elif self.cType == argType_double:
            data = unpack( "d", stream.read(8) )[0]           
        elif self.cType == argType_string:
            length = unpack( "I", stream.read(4) )[0]
            data = unpack( "%ds" % length, stream.read( length ) )[0]            
        elif self.cType == argType_dvmValue:
            data = dvmValue.decode( stream )        
        elif self.cType == argType_dvmList:
            data = dvmList.decode( stream )

        
        return hwiArg( self.cType, self.name, data )

    def copy( self ):
        # returns a copy of itself
        newArg = hwiArg( self.cType, self.name, None )

        newArg.set( self.get() )

        return newArg

    # Set the contents of this arg
    # N.B. This currently does no checking, so use with caution
    def set( self, data ):
        
        if self.cType == argType_int:
            self.vInt = data
            
        elif self.cType == argType_double:
            self.vDouble = data
            
        elif self.cType == argType_string:
            self.vString = data
            
        elif self.cType == argType_dvmValue:
            if isinstance(data, dvmValue):
                self.vDvmValue = data
            else:
                self.vDvmValue = dvmValue( data )
        
        elif self.cType == argType_dvmList:
            if isinstance(data, dvmList):
                self.vDvmList = data
            else:
                self.vDvmList = dvmList( data )
    
    # Get the contents of this arg
    def get( self ):
        
        if self.cType == argType_int:
            return self.vInt
            
        elif self.cType == argType_double:
            return self.vDouble
            
        elif self.cType == argType_string:
            return self.vString
            
        elif self.cType == argType_dvmValue:
            return self.vDvmValue
        
        elif self.cType == argType_dvmList:
            return self.vDvmList

class hwiArgList():
    def __init__( self, args=None ):
    
        if args is None:
            self.n = 0
            self.args = []  
    
        else:
            assert type( args ) is list, "hwiArgList initialised with wrong type for args: %r" % type( args )
            assert len( args ) <= 256, "hwiArgList initialised with too many args: %r" % len( args )
            
            self.n = len( args )
            self.args = args

    def __str__( self ):
        if self.n == 0:
            return "    <none>\n"
        
        output = ""
        for i in range( 0, self.n ):
            output = output + "    %i: " % (i+1) + str( self.args[i] ) + "\n"
        return output

    def encodeStructure( self, stream ):
        stream.write( pack( "I", self.n ) )
        for i in range( 0, self.n ):
            self.args[i].encodeStructure( stream )      

    def encodeData( self, stream ):
        for i in range( 0, self.n ):
            self.args[i].encodeData( stream )               

    @classmethod
    def decodeStructure( cls, stream ):

        # read 1 uint32 of number of args
        n = unpack( "I", stream.read(4) )[0]
        args = []
        for i in range( 0, n ):
            # read each arg in turn
            args.append( hwiArg.decodeStructure( stream ) )
    
        return cls( args )

    def decodeData( self, stream ):
        for i in range( 0, self.n ):
            self.args[i].decodeData( stream )

    def newDataInstanceFromStream( self, stream ):
        args = []
        for i in range( 0, self.n ):
            args.append( self.args[i].newDataInstanceFromStream( stream ) )

        return hwiArgList( args )

    def copy( self ):
        args = []
        for i in range( 0, self.n ):
            args.append( self.args[i].copy() )

        return hwiArgList( args )


class hwiFunction():

    def __init__( self, name, inputs, outputs, functionHandle=None ):
        assert type(name) is str, "hwiFunction called with name = %r" % type(name)
        assert len(name) <=64, "hwiFunction called with too long (>64) name: " % len(name)

        if inputs is not None:
            assert isinstance( inputs, hwiArgList ), "hwiFunction input arg list not an arg list"
        if outputs is not None:
            assert isinstance( outputs, hwiArgList ), "hwiFunction output arg list not an arg list"

        assert type( functionHandle ) is types.FunctionType or types.MethodType or None, "hwiFunction functionHandle is not a function type = %r"% type(functionHandle)

        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.functionHandle = functionHandle

    def __str__( self ):
        output = "  Function \'" + str( self.name ) + "\':\n"
        output += "   Input arguments:\n" + str( self.inputs )
        output += "   Output arguments:\n"  + str( self.outputs )

        return output

    def execute( self, server, inputs ):
        "Calls the associated function handle with the appropriate arguments"

        self.functionHandle( server, self, inputs )

    def encodeStructure( self, stream ):
        # send 64 bytes of name
        stream.write( pack( "64s", self.name ) )
        
        # send input argList
        if self.inputs is None:
            stream.write( pack( "I", 0 ) )
        else:
            self.inputs.encodeStructure( stream )
        
        # send output argList
        if self.outputs is None:
            stream.write( pack( "I", 0 ) )
        else:
            self.outputs.encodeStructure( stream )

    def encodeInputData( self, stream, inputs=None ):
        # send input argList
        if inputs is not None:
            inputs.encodeData( stream )
            
    def encodeOutputData( self, stream ):
        # send output argList
        if self.outputs is not None:
            self.outputs.encodeData( stream )


    @classmethod
    def decodeStructure( cls, stream ):
        # read 64 bytes of name
        rawName = unpack( "64s", stream.read(64) )[0]
        nullIndex = rawName.find('\0')
        name = rawName[ 0:nullIndex ]
        
        # read input argList
        inputs = hwiArgList.decodeStructure( stream )
        
        # read output argList
        outputs = hwiArgList.decodeStructure( stream )
        
        return cls( name, inputs, outputs )

    def decodeInputData( self, stream ):
        self.inputs.decodeData( stream )
        
    def decodeOutputData( self, stream ):
        self.outputs.decodeData( stream )

class hwiFunctionList():

    def __init__( self, functions ):
        assert type(functions) is list, "hwiFunctionList functions is not a list: %r" % type(n)

        self.n = len( functions )
        self.functions = functions

        # store the function index in the function type
        # this is done so that the function reply knows what index to send
        # it also means that a particular function definition can only be used once
        for i in range( 0, self.n ):
            self.functions[ i ].functionIndex = i

    def __str__( self ):
        output = "There are a total of %i functions:"
        for i in range( 0, self.n ):
            output = output + "\n" + str( self.functions[i] )
        return output


    def encodeStructure( self, stream ):
        # send 1 uint32 of number of functions
        stream.write( pack( "I", self.n ) )

        for i in range( 0, self.n ):
            # send each function in turn
            self.functions[i].encodeStructure( stream )

    @classmethod
    def decodeStructure( cls, stream ):
        # read 1 uint32 of number of functions
        n = unpack( "I", stream.read(4) )[0]
        functions = []
        for i in range( 0, n ):
            # read each function in turn
            functions.append( hwiFunction.decodeStructure( stream ) )
            functions[ i ].functionIndex = i
            
        return cls( functions )

