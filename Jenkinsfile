pipeline {
    agent any
    //{
      //  dockerfile {
	//	args "-v /etc/passwd:/etc/passwd"
	//	}
      //   }

    stages {
        stage('Hello') {
            steps {
                script{
                
                def image = docker.build('test:1.0')

                //docker.image('test:1.0').withRun(''){
                image.inside{
                    
        /* Run some tests which require MySQL */
                sh '''cd deployment
                      ls
                      pip install --no-cache-dir -r requirements.cdk.txt
                      cdk synth
                      cdk deploy
                      '''
                }
                }
                

                   
            }
        }
    }
}

