from fenics import *
import csv
import sys
import os
import sympy as sp
import json
import numpy as np


def write_to_csv(derived_quantities_dict, data):
    '''
    Exports data to csv according to parameters in derived_quantities_dict

    Arguments:
    - derived_quantities_dict: dict, contains derived quantities parameters
    - data: list, contains the data to be exported
    Returns:
    - True
    '''
    if "file" in derived_quantities_dict.keys():
        file_export = ''
        if "folder" in derived_quantities_dict.keys():
            file_export += derived_quantities_dict["folder"] + '/'
            os.makedirs(os.path.dirname(file_export), exist_ok=True)
        if derived_quantities_dict["file"].endswith(".csv"):
            file_export += derived_quantities_dict["file"]
        else:
            file_export += derived_quantities_dict["file"] + ".csv"
        busy = True
        while busy is True:
            try:
                with open(file_export, "w+") as f:
                    busy = False
                    writer = csv.writer(f, lineterminator='\n')
                    for val in data:
                        writer.writerows([val])
            except OSError as err:
                print("OS error: {0}".format(err))
                print("The file " + file_export + ".txt might currently be busy."
                      "Please close the application then press any key.")
                input()

    return True


def export_txt(filename, function, functionspace):
    '''
    Exports a 1D function into a txt file.
    Arguments:
    - filemame : str
    - function : fenics.Function()
    - functionspace: fenics.FunctionSpace()
    Returns:
    - True on sucess
    '''
    export = project(function, functionspace)
    busy = True
    x = interpolate(Expression('x[0]', degree=1), functionspace)
    while busy is True:
        try:
            np.savetxt(filename + '.txt', np.transpose(
                        [x.vector()[:], export.vector()[:]]))
            return True
        except OSError as err:
            print("OS error: {0}".format(err))
            print("The file " + filename + ".txt might currently be busy."
                  "Please close the application then press any key.")
            input()


def export_profiles(res, exports, t, dt, functionspace):
    '''
    Exports 1D profiles in txt files.
    Arguments:
    - res: list, contains fenics.Functions
    - exports: dict, contains parameters
    - t: float, time
    - dt: fenics.Constant(), stepsize
    - functionspace: fenics.FunctionSpace()
    Returns:
    - dt: fenics.Constant(), stepsize
    '''
    functions = exports['txt']['functions']
    labels = exports['txt']['labels']
    if len(functions) != len(labels):
        raise NameError("Number of functions to be exported "
                        "doesn't match number of labels in txt exports")
    if len(functions) > len(res):
        raise NameError("Too many functions to export "
                        "in txt exports")
    solution_dict = {
        'solute': res[0],
        'retention': res[len(res)-2],
        'T': res[len(res)-1],
    }
    times = sorted(exports['txt']['times'])
    end = True
    for time in times:
        if t == time:
            if times.index(time) != len(times)-1:
                next_time = times[times.index(time)+1]
                end = False
            else:
                end = True
            for i in range(len(functions)):
                if functions[i].isdigit() is True:
                    solution = res[int(functions[i])]
                elif functions[i] in solution_dict:
                    solution = solution_dict[functions[i]]
                else:
                    raise ValueError(
                        "function " + functions[i] + " is unknown")
                label = labels[i]
                export_txt(
                    exports["txt"]["folder"] + '/' + label + '_' +
                    str(t) + 's',
                    solution, functionspace)
            break
        if t < time:
            next_time = time
            end = False
            break
    if end is False:
        if t + float(dt) > next_time:
            dt.assign(time - t)
    return dt


def define_xdmf_files(exports):
    '''
    Returns a list of XDMFFile
    Arguments:
    - exports: dict, contains parameters
    Returns:
    - files: list, contains the fenics.XDMFFile() objects
    '''
    if len(exports['xdmf']['functions']) != len(exports['xdmf']['labels']):
        raise NameError("Number of functions to be exported "
                        "doesn't match number of labels in xdmf exports")
    if exports["xdmf"]["folder"] == "":
        raise ValueError("folder value cannot be an empty string")
    if type(exports["xdmf"]["folder"]) is not str:
        raise TypeError("folder value must be of type str")
    files = list()
    for i in range(0, len(exports["xdmf"]["functions"])):
        u_file = XDMFFile(exports["xdmf"]["folder"]+'/' +
                          exports["xdmf"]["labels"][i] + '.xdmf')
        u_file.parameters["flush_output"] = True
        u_file.parameters["rewrite_function_mesh"] = False
        files.append(u_file)
    return files


def export_xdmf(res, exports, files, t, append):
    '''
    Exports the solutions fields in xdmf files.
    Arguments:
    - res: list, contains fenics.Function()
    - exports: dict, contains parameters
    - files: list, contains fenics.XDMFFile()
    - t: float, time
    - append: bool, erase the previous file or not
    '''
    if len(exports['xdmf']['functions']) > len(res):
        raise NameError("Too many functions to export "
                        "in xdmf exports")
    solution_dict = {
        'solute': res[0],
        'retention': res[len(res)-2],
        'T': res[len(res)-1],
    }
    for i in range(0, len(exports["xdmf"]["functions"])):
        label = exports["xdmf"]["labels"][i]
        fun = exports["xdmf"]["functions"][i]
        if type(fun) is int:
            if fun <= len(res):
                solution = res[fun]
            else:
                raise ValueError(
                    "The value " + str(fun) +
                    " is unknown.")
        elif type(fun) is str:
            if fun.isdigit():
                fun = int(fun)
                if fun <= len(res):
                    solution = res[fun]
                else:
                    raise ValueError(
                        "The value " + str(fun) +
                        " is unknown.")
            elif fun in solution_dict.keys():
                solution = solution_dict[fun]
            else:
                raise ValueError(
                    "The value " + fun +
                    " is unknown.")
        else:
            raise TypeError('Unexpected' + str(type(fun)) + 'type')

        solution.rename(label, "label")
        checkpoint = True  # Default value
        if "checkpoint" in exports["xdmf"].keys():
            if type(exports["xdmf"]["checkpoint"]) != bool:
                raise TypeError(
                    "Unknown value for XDMF checkpoint (True or False)")
            if exports["xdmf"]["checkpoint"] is False:
                checkpoint = False

        if checkpoint:
            files[i].write_checkpoint(
                solution, label, t, XDMFFile.Encoding.HDF5, append=append)
        else:
            files[i].write(solution, t)
    return


def treat_value(d):
    '''
    Recursively converts as string the sympy objects in d
    Arguments: d, dict
    Returns: d, dict
    '''

    T = sp.symbols('T')
    if type(d) is dict:
        d2 = {}
        for key, value in d.items():
            if isinstance(value, tuple(sp.core.all_classes)):
                value = str(sp.printing.ccode(value))
                d2[key] = value
            elif callable(value):  # if value is fun
                d2[key] = str(sp.printing.ccode(value(T)))
            elif type(value) is dict or type(value) is list:
                d2[key] = treat_value(value)
            else:
                d2[key] = value
    elif type(d) is list:
        d2 = []
        for e in d:
            e2 = treat_value(e)
            d2.append(e2)
    else:
        d2 = d

    return d2


def export_parameters(parameters):
    '''
    Dumps parameters dict in a json file.
    '''
    json_file = parameters["exports"]["parameters"]
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    if json_file.endswith(".json") is False:
        json_file += ".json"
    param = treat_value(parameters)
    with open(json_file, 'w') as fp:
        json.dump(param, fp, indent=4, sort_keys=True)
    return True
