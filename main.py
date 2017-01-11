if __name__ == "__main__":
    import assembly_trinity_test as assembly
    import dibMMETSP_configuration as dib_conf



    # Assembly of data
    data_dir = dib_conf.data_dir
    datafiles = [dib_conf.sra_csv]
    trinity_fail = []
    count = 0
    for datafile in datafiles:
        trinity_fail, count = assembly.execute(trinity_fail, count, data_dir)
    print("Number of Trinity assemblies:", count)
    print("Total number of times Trinity failed:", len(trinity_fail), trinity_fail)
