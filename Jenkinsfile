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

                docker.image('test:1.0').withRun('-u root:root '){
                //image.inside
                    
        /* Run some tests which require MySQL */
                sh '''cd deployment
                      ls
                      python -m pip install -r requirements.cdk.txt
                      cdk synth
                      cdk deploy
                      '''
                }
                }
                

                   
            }
        }
    }
}

