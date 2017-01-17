if __name__ == "__main__":
    import getdata as data
    import trim_qc as trim
    import diginorm_mmetsp as diginorm
    import assembly_trinity as assembly
    import dibMMETSP_configuration as dib_conf
    import clusterfunc
    # set working directories
    data_dir = dib_conf.data_dir
    clusterfunc.check_dir(data_dir)
    datafiles = [dib_conf.sra_csv]
    trinity_fail = []
    count = 0
    for datafile in datafiles:
        # get data
        url_data=data.get_data_dict(datafile)
        print(url_data)
        # get data from NCBI
        data.execute(data_dir,url_data)
        # run trim, qc
        trim.execute(url_data,data_dir)
        # diginormdir
        diginorm.execute(data_dir, url_data)
        # Assembly of data
        trinity_fail, count = assembly.execute(trinity_fail, count, data_dir)
    print("Number of Trinity assemblies completed:", count)
    print("Total number of times Trinity failed:", len(trinity_fail), trinity_fail)
    print("Total MMETSP samples:",len(url_data))
