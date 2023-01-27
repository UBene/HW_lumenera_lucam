class LucamH5Loader:
    def __init__(self, filename:str):
        self.filename=filename
        
        with h5py.File(filename) as file:
            M = file['measurement/lucam']
            self.image = M['image'][:]
            self.imshow_extent = M['imshow_extent'][:]
            H = file['hardware/lucam']
            self.exposure = H['settings'].attrs['exposure']
            self.pixel_format = H['settings'].attrs['pixel_format']

        
    def default_plot(self):
        print(self.filename, 'exposure', self.exposure)
        if self.pixel_format == 0:
            image = self.image*1.0
        
        if self.pixel_format == 1:
            image = self.image/2**8
            
        plt.imshow(image.swapaxes(0,1)[:,:,2]) 
        plt.colorbar()
        return plt.gca()